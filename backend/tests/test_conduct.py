"""Conduct engine tests. The LLM is faked at the client boundary, so every assertion
here is about the engine's own decisions: what it offers, what it accepts, what it
refuses, and where run state lives.
"""

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast

import pytest

from app.conduct.engine import (
    MAX_FOLLOW_UPS,
    MAX_REPLIES,
    TRANSCRIPT_WINDOW,
    ConductEngine,
    _transcript,
)
from app.conduct.repository import RunRepository
from app.errors import ConflictError, ForbiddenError
from app.llm import ledger
from app.llm.client import LLMError, NoToolCallError, ToolTurn
from app.runs.enums import AnswerKind, MessageRole, RunStatus
from app.runs.models import RunMessage, SurveyRun
from app.templates.enums import AnswerType
from app.templates.schemas import QuestionInput, TemplateCreate, TemplateUpdate
from app.templates.service import TemplateService
from tests.fakes import FakeLLM
from tests.fakes import follow_up as _follow_up
from tests.fakes import move_on as _move_on
from tests.fakes import record as _record
from tests.fakes import reply as _reply


async def test_start_opens_with_the_first_question(session, respondent, published):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    assert run.status is RunStatus.in_progress
    assert run.current_question_index == 0
    assert len(run.messages) == 1
    assert "What's your role?" in run.messages[0].content


async def test_records_answer_then_advances(session, respondent, published):
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    # q0 permits probing, so after recording the engine loops once for the probe decision.
    llm = FakeLLM(_record("Line lead"), _move_on("Thanks. How was onboarding?"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    assert llm.calls == 2
    assert run.current_question_index == 1
    scripted = [a for a in run.answers if a.kind is AnswerKind.scripted]
    assert len(scripted) == 1
    assert scripted[0].value == {"text": "Line lead"}
    assert run.messages[-1].content == "Thanks. How was onboarding?"


async def test_engine_withholds_follow_up_once_the_cap_is_spent(session, respondent, published):
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    # Answer, then probe. Twice — that exhausts the cap.
    for reply in ("What does that involve?", "Anything else?"):
        llm = FakeLLM(_record("Line lead"), _follow_up(reply))
        run = await ConductEngine(session, llm=llm).handle_message(run.id, "…", respondent)
        assert run.current_question_index == 0  # a follow-up must not advance the survey
        assert run.messages[-1].content == reply

    # The third answer lands with the cap spent, so ask_follow_up is no longer offered.
    llm = FakeLLM(_record("Not really"), _move_on())
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "no", respondent)

    assert "ask_follow_up" not in llm.offered[-1]
    assert len([a for a in run.answers if a.kind is AnswerKind.follow_up]) == MAX_FOLLOW_UPS
    assert run.current_question_index == 1


async def test_follow_up_beyond_the_cap_is_rejected_in_code(session, respondent, published):
    """Even if the model ignores the offered toolset, the engine refuses."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    for _ in range(MAX_FOLLOW_UPS):
        run = await ConductEngine(
            session, llm=FakeLLM(_record("x"), _follow_up("more?"))
        ).handle_message(run.id, "…", respondent)

    llm = FakeLLM(_follow_up("one more?"))
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=llm).handle_message(run.id, "no", respondent)
    assert llm.calls == 2  # the rejected probe and its one retry


async def test_the_cap_counts_probes_asked_not_answers_recorded(session, respondent, published):
    """A respondent who never answers a probe must still exhaust the budget.

    The cap is spent when the engine issues a follow-up. Counting recorded answers
    instead would let a model probe forever as long as no reply was ever recorded,
    each probe costing another paid call with the whole transcript resent.
    """
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    # Answer once, then probe — that is probe 1.
    first = FakeLLM(_record("Line lead"), _follow_up("What does that involve?"))
    run = await ConductEngine(session, llm=first).handle_message(run.id, "line lead", respondent)

    # Reply evasively; the model probes again without recording anything. Probe 2.
    second = FakeLLM(_follow_up("Could you say a bit more?"))
    run = await ConductEngine(session, llm=second).handle_message(
        run.id, "dunno really", respondent
    )

    assert run.probes_asked == {published_question_id(run): MAX_FOLLOW_UPS}
    assert not [a for a in run.answers if a.kind is AnswerKind.follow_up]  # nothing recorded

    # The budget is now spent even though no follow-up answer exists.
    third = FakeLLM(_follow_up("And anything else?"))
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=third).handle_message(run.id, "still dunno", respondent)
    assert "ask_follow_up" not in third.offered[-1]


def published_question_id(run):
    """The first question's id, as the engine keys probes_asked by."""
    return next(iter(run.probes_asked))


async def test_invalid_value_retries_once_then_fails_loudly(session, respondent, published):
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    first = FakeLLM(_record("Line lead"), _move_on())
    run = await ConductEngine(session, llm=first).handle_message(run.id, "line lead", respondent)
    assert run.current_question_index == 1  # now on the rating question

    llm = FakeLLM(_record("eleven"))  # a rating must be an int 1-5
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=llm).handle_message(run.id, "eleven!", respondent)

    assert llm.calls == 2  # one retry, then loud failure
    assert run.current_question_index == 1  # no silent default, no advance
    assert len(run.answers) == 1


async def test_malformed_tool_output_is_rejected(session, respondent, published):
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    garbage = ToolTurn(text="", tool_name="record_answer", tool_input={"nonsense": True})
    llm = FakeLLM(garbage)
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=llm).handle_message(run.id, "hello", respondent)
    assert llm.calls == 2


async def test_unknown_tool_name_is_rejected(session, respondent, published):
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    invented = ToolTurn(text="", tool_name="skip_survey", tool_input={})
    llm = FakeLLM(invented)
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=llm).handle_message(run.id, "hello", respondent)
    assert llm.calls == 2


async def test_declining_a_question_advances_it(session, respondent, published):
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    decline = ToolTurn(
        text="No problem. How was onboarding?",
        tool_name="flag_unanswerable",
        tool_input={"reason": "respondent declined"},
    )
    run = await ConductEngine(session, llm=FakeLLM(decline)).handle_message(
        run.id, "rather not say", respondent
    )
    assert run.current_question_index == 1
    assert run.answers[0].value == {"unanswerable": "respondent declined"}


async def test_run_completes_after_the_final_question(session, respondent, published):
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    first = FakeLLM(_record("Line lead"), _move_on())
    run = await ConductEngine(session, llm=first).handle_message(run.id, "line lead", respondent)
    # The rating question forbids follow-ups, so one recorded answer completes the run.
    llm = FakeLLM(_record(4, "Thanks, that's everything."))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "four", respondent)

    assert llm.calls == 1
    assert run.status is RunStatus.completed
    assert run.completed_at is not None
    assert [a.value for a in run.answers if a.kind is AnswerKind.scripted] == [
        {"text": "Line lead"},
        {"rating": 4},
    ]

    with pytest.raises(ConflictError):  # a finished run takes no more messages
        await ConductEngine(session, llm=FakeLLM()).handle_message(run.id, "more", respondent)


async def test_republishing_leaves_an_in_flight_run_alone(session, author, respondent, published):
    """A run is bound to the version it started on, so authors can keep editing."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    first = FakeLLM(_record("Line lead"), _move_on())
    run = await ConductEngine(session, llm=first).handle_message(run.id, "line lead", respondent)

    # The author rewrites the survey and republishes while the respondent is mid-run.
    svc = TemplateService(session)
    await svc.update_draft(
        published.id,
        TemplateUpdate(
            title="Something else entirely",
            questions=[
                QuestionInput(text="A brand new question", answer_type=AnswerType.long_text)
            ],
        ),
        author,
    )
    assert (await svc.publish(published.id, author)).version == 2

    reloaded = ConductEngine(session, llm=FakeLLM())
    live = await reloaded.load(run.id, respondent)
    assert [q["text"] for q in await reloaded.questions(live)] == [
        "What's your role?",
        "Rate your onboarding",
    ]
    assert live.current_question_index == 1  # position untouched by the republish

    # And it still completes against v1's questions, not the new ones.
    llm = FakeLLM(_record(4, "Thanks, that's everything."))
    live = await ConductEngine(session, llm=llm).handle_message(live.id, "four", respondent)
    assert live.status is RunStatus.completed
    assert [a.value for a in live.answers if a.kind is AnswerKind.scripted] == [
        {"text": "Line lead"},
        {"rating": 4},
    ]


def _decline(reason: str = "respondent declined", say: str = "No problem.") -> ToolTurn:
    return ToolTurn(text=say, tool_name="flag_unanswerable", tool_input={"reason": reason})


async def test_declining_a_follow_up_moves_the_survey_on(session, respondent, published):
    """Found by a live run: "rather not say" to a probe used to exhaust the turn loop.

    flag_unanswerable was only offered before the scripted answer existed, so once a
    probe was outstanding the model had no way to say the respondent had declined.
    """
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    probe = FakeLLM(_record("Line lead"), _follow_up("What does that involve?"))
    run = await ConductEngine(session, llm=probe).handle_message(run.id, "line lead", respondent)

    llm = FakeLLM(_decline("would rather not say"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "rather not say", respondent)

    assert "flag_unanswerable" in llm.offered[0]  # offered while a probe is outstanding
    assert run.current_question_index == 1  # the survey moved on rather than stalling
    declined = [a for a in run.answers if a.kind is AnswerKind.follow_up]
    assert declined[0].value == {"unanswerable": "would rather not say"}
    assert declined[0].question_text == "What does that involve?"  # the probe, not the question


async def test_only_one_answer_is_recorded_per_respondent_message(session, respondent, published):
    """Recording neither advances nor spends a probe, so repeats would spin the loop."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("Line lead"), _record("Line lead again"), _record("and again"))
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    assert "record_answer" in llm.offered[0]
    assert "record_answer" not in llm.offered[-1]  # withdrawn after the first record


async def test_briefing_dates_the_conversation_and_marks_optional_questions(
    session, author, respondent
):
    """Both found by a live run.

    The model resolved "the 3rd of March this year" against its training data and recorded
    2024-03-03. Separately, asked an optional question it had no way to know was optional,
    it turned "hard to say really" into a rating of 3 rather than letting it go.
    """
    svc = TemplateService(session)
    template = await svc.create_draft(
        TemplateCreate(
            title="Starters",
            questions=[
                QuestionInput(text="When did you start?", answer_type=AnswerType.date),
                QuestionInput(
                    text="Still here in two years?",
                    answer_type=AnswerType.rating,
                    required=False,
                ),
            ],
        ),
        author,
    )
    await svc.publish(template.id, author)

    fake = FakeLLM(_record("2026-03-03"), _move_on(), _record(3), _move_on())
    engine = ConductEngine(session, llm=fake)
    run = await engine.start_run(template.id, respondent)
    await engine.handle_message(run.id, "3rd of March this year", respondent)
    await engine.handle_message(run.id, "hard to say really", respondent)

    now = datetime.now(UTC)
    assert f"Today is {now:%A}, {now.date().isoformat()}" in fake.briefings[0]
    assert "- This question is required" in fake.briefings[0]

    optional = fake.briefings[-1]
    assert "Today is" not in optional  # only where it can matter
    assert "This question is OPTIONAL" in optional


async def test_can_probe_before_any_answer_is_recorded(session, respondent, published):
    """Found by a live run: the model wrote `"placeholder"` to unlock ask_follow_up.

    Probing used to require a scripted answer to exist, so a model wanting to clarify a
    vague reply had to invent one first. The reply to such a probe is the scripted answer,
    since the probe was asking for the question's own answer.
    """
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    probe = FakeLLM(_follow_up("Which team are you on day to day?"))
    run = await ConductEngine(session, llm=probe).handle_message(run.id, "hard to say", respondent)

    assert "ask_follow_up" in probe.offered[0]
    assert not run.answers  # nothing invented to unlock the probe
    assert run.current_question_index == 0
    assert run.messages[-1].content == "Which team are you on day to day?"

    answer = FakeLLM(_record("Line lead"), _move_on())
    run = await ConductEngine(session, llm=answer).handle_message(run.id, "line lead", respondent)

    scripted = [a for a in run.answers if a.kind is AnswerKind.scripted]
    assert [a.value for a in scripted] == [{"text": "Line lead"}]
    assert run.current_question_index == 1


async def test_state_survives_a_reload(session, respondent, published):
    """Run position lives in the database, not in the model's head or the client's."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    await ConductEngine(session, llm=FakeLLM(_record("Line lead"), _move_on())).handle_message(
        run.id, "line lead", respondent
    )

    reloaded = await ConductEngine(session, llm=FakeLLM()).load(run.id, respondent)
    assert reloaded.current_question_index == 1
    assert reloaded.status is RunStatus.in_progress
    assert [m.role.value for m in reloaded.messages] == ["assistant", "user", "assistant"]


# ---------------------------------------------------------------- tricky input


async def test_reply_speaks_without_recording_or_advancing(session, respondent, published):
    """A respondent asking a question back gets an answer, not a fabricated record."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_reply("It just means your job title — whatever you'd call it."))
    run = await ConductEngine(session, llm=llm).handle_message(
        run.id, "what do you mean by role?", respondent
    )

    assert "reply" in llm.offered[0]
    assert not run.answers
    assert run.current_question_index == 0
    assert run.messages[-1].content == "It just means your job title — whatever you'd call it."


async def test_reply_cap_withholds_the_tool(session, respondent, published):
    """Replies are budgeted per question so a chatty model cannot stall the survey."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    for _ in range(MAX_REPLIES):
        run = await ConductEngine(session, llm=FakeLLM(_reply("Sure —"))).handle_message(
            run.id, "wait, what?", respondent
        )

    llm = FakeLLM(_record("Line lead"), _move_on())
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)
    assert "reply" not in llm.offered[0]
    assert run.current_question_index == 1  # the survey still moves


async def test_cross_question_tool_call_is_rejected(session, respondent, published):
    """Answering a different question than the current one (two answers at once, or a
    revision of an earlier answer) is refused; a placeholder id passes through."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    questions = await ConductEngine(session, llm=FakeLLM()).questions(run)
    other_id = questions[1]["id"]

    cross = ToolTurn(
        text="", tool_name="record_answer", tool_input={"question_id": other_id, "value": "4"}
    )
    llm = FakeLLM(cross)
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=llm).handle_message(run.id, "and I'd say 4", respondent)
    assert llm.calls == 2  # rejected, retried, failed loudly
    assert not run.answers

    placeholder = ToolTurn(
        text="", tool_name="record_answer", tool_input={"question_id": "q", "value": "Line lead"}
    )
    run = await ConductEngine(session, llm=FakeLLM(placeholder, _move_on())).handle_message(
        run.id, "line lead", respondent
    )
    assert [a.value for a in run.answers] == [{"text": "Line lead"}]


async def test_blank_unanswerable_reason_is_defaulted_not_rejected(session, respondent, published):
    """The reason is metadata; a weak model omitting it should not burn the retry."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    bare = ToolTurn(text="", tool_name="flag_unanswerable", tool_input={"question_id": "q"})
    llm = FakeLLM(bare)
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "skip", respondent)

    assert llm.calls == 1  # no retry spent
    assert run.current_question_index == 1
    assert run.answers[0].value == {"unanswerable": "respondent declined"}


async def test_record_tool_carries_a_typed_value_schema(session, respondent, published):
    """Constrained backends get a grammar for the value, not just prose."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("Line lead"), _move_on())
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    record = next(t for t in llm.tools_seen[0] if t["name"] == "record_answer")
    assert record["input_schema"]["properties"]["value"]["type"] == "string"  # short_text

    rating = FakeLLM(_record(4), _move_on())
    await ConductEngine(session, llm=rating).handle_message(run.id, "a solid 4", respondent)
    record = next(t for t in rating.tools_seen[0] if t["name"] == "record_answer")
    value = record["input_schema"]["properties"]["value"]
    assert (value["type"], value["minimum"], value["maximum"]) == ("integer", 1, 5)


async def test_rejection_feedback_reaches_the_model_in_band(session, respondent, published):
    """Small models weight the last user message, not a line at the tail of the system
    prompt — so the retry must carry the correction in the transcript itself."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    run = await ConductEngine(
        session, llm=FakeLLM(_record("Line lead"), _move_on())
    ).handle_message(run.id, "line lead", respondent)

    llm = FakeLLM(_record("eleven"), _record(4), _move_on())
    await ConductEngine(session, llm=llm).handle_message(run.id, "eleven!", respondent)

    retry_messages = llm.messages_seen[1]
    assert retry_messages[-1]["role"] == "user"
    assert "[engine]" in retry_messages[-1]["content"]
    assert "rejected" in retry_messages[-1]["content"]


def test_transcript_is_windowed_for_small_contexts():
    """A long run must not replay unbounded history: the briefing restates the current
    question every turn, so only a recent window is needed."""
    run = SimpleNamespace(
        messages=[RunMessage(role=MessageRole.user, content=f"message {i}") for i in range(30)]
    )
    windowed = _transcript(cast("SurveyRun", run))
    assert len(windowed) == TRANSCRIPT_WINDOW + 1
    assert windowed[0]["content"] == "[earlier conversation omitted]"
    assert windowed[-1]["content"] == "message 29"


def test_transcript_always_opens_on_a_user_turn():
    """The old Anthropic tier rejected a message list starting with the assistant, and
    every run opens with the engine's greeting, so a run's first few turns 400'd there and
    fell through to the next tier. Only the windowed path escaped, its head being a user
    message. That tier is gone; the invariant is kept because an assistant-first list is
    the odd thing to hand any provider."""
    for length in range(1, TRANSCRIPT_WINDOW + 6):
        run = SimpleNamespace(
            messages=[
                RunMessage(
                    role=MessageRole.assistant if i % 2 == 0 else MessageRole.user,
                    content=f"message {i}",
                )
                for i in range(length)
            ]
        )
        sent = _transcript(cast("SurveyRun", run))
        assert sent[0]["role"] == "user", f"{length} stored messages opened on the assistant"

    # The real opening shape: greeting, then the respondent's first reply.
    run = SimpleNamespace(
        messages=[
            RunMessage(role=MessageRole.assistant, content="Thanks for taking it. Your role?"),
            RunMessage(role=MessageRole.user, content="Data engineer"),
        ]
    )
    sent = _transcript(cast("SurveyRun", run))
    assert [m["role"] for m in sent] == ["user", "assistant", "user"]
    assert sent[1]["content"].endswith("Your role?")  # the greeting is still replayed


def test_whitespace_only_messages_are_refused_at_the_boundary():
    """A blank message must 422 before it reaches the transcript or burns a model turn."""
    from pydantic import ValidationError

    from app.conduct.schemas import RunMessageRequest

    assert RunMessageRequest(content="  real words  ").content == "real words"
    with pytest.raises(ValidationError):
        RunMessageRequest(content="   ")


async def test_a_chatty_turn_with_no_tool_call_is_retried_once(session, respondent, published):
    """A live run died mid-survey on 'Backup LLM returned no tool call' — the model was
    responsive, it just talked instead of acting. That is cheaply retryable with an
    in-band nudge; a second offence still fails loudly."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    recovers = FakeLLM(NoToolCallError("no tool"), _record("Line lead"), _move_on())
    run = await ConductEngine(session, llm=recovers).handle_message(run.id, "line lead", respondent)
    assert recovers.calls == 3  # chatted, nudged retry recorded, then moved on
    assert "exactly one of the offered tools" in recovers.messages_seen[1][-1]["content"]
    assert [a.value for a in run.answers] == [{"text": "Line lead"}]

    stubborn = FakeLLM(NoToolCallError("no tool"), NoToolCallError("still no tool"))
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=stubborn).handle_message(run.id, "4", respondent)
    assert stubborn.calls == 2  # one nudge, then loud failure — never an infinite loop


async def test_a_second_turn_is_refused_while_one_is_in_flight(
    engine, session, respondent, published
):
    """The lock is the whole mechanism, so test it directly rather than by timing.

    A run holds its row for the length of a turn — which spans a model call — so the
    second arrival is told the run is busy instead of waiting on it.
    """
    from sqlalchemy.ext.asyncio import AsyncSession

    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    await session.commit()

    async with AsyncSession(engine, expire_on_commit=False) as holder:
        assert await RunRepository(holder).try_lock(run.id)  # first turn owns the run

        async with AsyncSession(engine, expire_on_commit=False) as second:
            engine_two = ConductEngine(second, llm=FakeLLM(_record("Line lead")))
            with pytest.raises(ConflictError, match="already handling"):
                await engine_two.handle_message(run.id, "line lead", respondent)


async def test_racing_messages_never_double_answer_one_question(
    engine, session, respondent, published
):
    """A double-clicked send used to leave two scripted answers on one question, and the
    author's results then read '2 of 2 answered' on a run whose second question was never
    asked. Whoever wins, the run must hold one scripted answer per question."""
    import asyncio

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.runs.models import Answer

    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    await session.commit()

    class SlowLLM:
        """Holds the first turn open long enough for the second request to arrive.

        q0 permits probing, so the engine loops once after recording — hence move_on on
        the second call, exactly as the scripted fakes elsewhere do.
        """

        def __init__(self) -> None:
            self.calls = 0

        async def tool_turn(self, **_):
            self.calls += 1
            if self.calls == 1:
                await asyncio.sleep(0.05)
                return _record("Line lead")
            return _move_on()

        async def tool_call(self, **_):
            raise AssertionError("unused")

    async def turn(n: int):
        async with AsyncSession(engine, expire_on_commit=False) as s:
            try:
                await ConductEngine(s, llm=SlowLLM()).handle_message(run.id, f"m{n}", respondent)
                return "ok"
            except ConflictError:
                return "refused"

    outcomes = await asyncio.gather(turn(1), turn(2))
    assert outcomes.count("refused") == 1, outcomes

    async with AsyncSession(engine, expire_on_commit=False) as s:
        rows = (await s.execute(select(Answer).where(Answer.run_id == run.id))).scalars().all()
    scripted = [a for a in rows if a.kind is AnswerKind.scripted]
    assert len(scripted) == 1
    assert len({a.question_id for a in scripted}) == 1


# ------------------------------------------------------------------- language


async def test_a_run_pins_its_language_at_the_start(session, respondent, published):
    """Fixed when the run begins, not read per request: a respondent resuming on
    another device, or after their browser's language changed, must not find the
    interview switching language with a transcript above them in the first one."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent, language="pl")
    assert run.language == "pl"

    # Reloading is the resume path, and it reads the stored value.
    resumed = await engine.load(run.id, respondent)
    assert resumed.language == "pl"


async def test_a_run_defaults_to_english(session, respondent, published):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    assert run.language == "en"


async def test_the_run_language_reaches_the_model(session, respondent, published):
    """The instruction is injected per run rather than baked into the prompt file, so
    this is the only thing proving it actually arrives."""
    llm = FakeLLM(_record("Line lead"), _move_on())
    engine = ConductEngine(session, llm=llm)
    run = await engine.start_run(published.id, respondent, language="es")
    await engine.handle_message(run.id, "soy jefe de línea", respondent)

    assert llm.briefings, "the model was never asked anything"
    assert "Speak Spanish" in llm.briefings[0]


async def test_an_answer_in_another_language_still_stores_a_typed_value(
    session, respondent, published
):
    """What makes a multilingual interview a prompt problem rather than a parser one:
    the model reads "cuatro" and the tool call carries 4, so nothing downstream needs
    to know which language the run was in."""
    llm = FakeLLM(_record("Line lead"), _move_on(), _record(4), _move_on())
    engine = ConductEngine(session, llm=llm)
    run = await engine.start_run(published.id, respondent, language="es")
    await engine.handle_message(run.id, "soy jefe de línea", respondent)
    run = await engine.handle_message(run.id, "cuatro", respondent)

    stored = [a.value for a in run.answers if a.kind is AnswerKind.scripted]
    assert {"rating": 4} in stored


async def test_the_engines_own_closing_line_follows_the_run_language(
    session, respondent, published
):
    """The distinction this stage settled on: the engine's own sentences are
    translated, the author's question text is not. Nobody wrote the closing line, so
    saying it in the respondent's language costs nothing; a question's wording is the
    survey itself, and rendering that in another language is content translation with
    a data model behind it."""
    from app.i18n import translate

    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent, language="es")

    # Answer every question with no closing line of the model's own, so the engine
    # falls back to its own words.
    silent_move_on = ToolTurn(text="", tool_name="move_on", tool_input={})
    for value in ("Line lead", 4, "Days"):
        # Silent on both turns: the fake's default "Thanks." would otherwise be the
        # last thing said, and this test is about what the engine says when the model
        # says nothing.
        silent_record = ToolTurn(text="", tool_name="record_answer", tool_input={"value": value})
        llm = FakeLLM(silent_record, silent_move_on)
        run = await ConductEngine(session, llm=llm).handle_message(run.id, "…", respondent)
        if run.status is RunStatus.completed:
            break

    assert run.status is RunStatus.completed
    assert run.messages[-1].content == translate("closing", "es")
    assert run.messages[-1].content != translate("closing", "en")


# ------------------------------------------------- follow-ups answer in their own shape


async def test_a_follow_up_to_a_yes_no_question_records_the_words(
    session, respondent, published_yes_no
):
    """Found by conducting a real survey, not by this suite.

    A probe is a new question the model wrote, and it is usually open: "could you
    describe the issues you've encountered?". Validated against the scripted question's
    type, the only legal answer to that was a boolean, so the description was never
    sent and the author's results showed the word "yes".
    """
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published_yes_no.id, respondent)

    llm = FakeLLM(_record(True), _follow_up("Could you describe the issues?"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "yes", respondent)

    llm = FakeLLM(_record("The scanner drops its connection every few hours."), _move_on())
    run = await ConductEngine(session, llm=llm).handle_message(
        run.id, "the scanner drops out", respondent
    )

    follow_ups = [a for a in run.answers if a.kind is AnswerKind.follow_up]
    assert len(follow_ups) == 1
    assert follow_ups[0].value == {"text": "The scanner drops its connection every few hours."}


async def test_a_follow_up_that_re_asks_the_question_stays_structured(
    session, respondent, published_yes_no
):
    """The other half of the rule. A probe that re-asks the scripted question should
    record the option, not the word for it, so results stay analysable."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published_yes_no.id, respondent)

    llm = FakeLLM(_record(True), _follow_up("Just to confirm, is that a yes?"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "yes", respondent)

    llm = FakeLLM(_record(False), _move_on())
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "no actually", respondent)

    follow_ups = [a for a in run.answers if a.kind is AnswerKind.follow_up]
    assert follow_ups[0].value == {"yes_no": False}


async def test_the_follow_up_gate_still_refuses_nonsense(session, respondent, published_yes_no):
    """Prose is legitimate; the gate is not optional. A value that is neither the
    question's shape nor text is still rejected and retried."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published_yes_no.id, respondent)

    llm = FakeLLM(_record(True), _follow_up("Could you describe the issues?"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "yes", respondent)

    llm = FakeLLM(_record({"nested": "object"}))
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=llm).handle_message(run.id, "…", respondent)


async def test_a_follow_up_is_offered_both_shapes(session, respondent, published_yes_no):
    """The schema is what made this possible: with only the parent's shape on offer the
    model had no way to send prose, whatever the recording rule said."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published_yes_no.id, respondent)

    llm = FakeLLM(_record(True), _follow_up("Could you describe the issues?"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "yes", respondent)

    probe = FakeLLM(_record("because the scanner drops out"), _move_on())
    await ConductEngine(session, llm=probe).handle_message(run.id, "…", respondent)

    record_tool = next(t for t in probe.tools_seen[0] if t["name"] == "record_answer")
    shapes = record_tool["input_schema"]["properties"]["value"]["anyOf"]
    assert {"type": "string"} in shapes


# ------------------------------------------------- taking back the previous answer


async def _publish(session, author, *questions: QuestionInput):
    """A published survey from questions given inline, for shapes only one test needs."""
    svc = TemplateService(session)
    template = await svc.create_draft(
        TemplateCreate(title="Rewind check", questions=list(questions)), author
    )
    await svc.publish(template.id, author)
    return template


async def test_rewind_takes_back_the_answer_and_the_turn_that_gave_it(
    session, respondent, published
):
    """A one-word answer the respondent wanted back. The engine refuses the *model* any
    action on an earlier question; this is the respondent asking, and it is the only way
    back. Afterwards the run sits exactly where it did before the answer."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    opening = run.messages[0].content

    llm = FakeLLM(_record("Line lead"), _move_on("Thanks. Rate your onboarding."))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)
    assert run.current_question_index == 1

    # No scripted turns: a rewind is pure state, and must not spend a model call.
    run = await ConductEngine(session, llm=FakeLLM()).rewind_last_answer(run.id, respondent)

    assert run.current_question_index == 0
    assert run.answers == []
    assert [m.content for m in run.messages] == [opening]


async def test_rewind_drops_the_follow_ups_that_hung_off_the_answer(session, respondent, published):
    """A probe's answer only means anything next to the answer that earned it. Leaving it
    behind would show the author a follow-up attached to a question nobody answered."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("Line lead"), _follow_up("What does that involve?"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)
    llm = FakeLLM(_record("Running the line"), _move_on("Thanks."))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "running it", respondent)
    assert len(run.answers) == 2

    run = await ConductEngine(session, llm=FakeLLM()).rewind_last_answer(run.id, respondent)

    assert run.answers == []
    assert run.current_question_index == 0


async def test_rewind_refunds_the_probe_budget(session, respondent, published):
    """The question is asked afresh, not continued, so a second answer worth probing
    deserves the probes the first one spent. Without the refund the retry is mute."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    for probe in ("What does that involve?", "Anything else?"):
        llm = FakeLLM(_record("Line lead"), _follow_up(probe))
        run = await ConductEngine(session, llm=llm).handle_message(run.id, "…", respondent)
    assert run.probes_asked != {}

    run = await ConductEngine(session, llm=FakeLLM()).rewind_last_answer(run.id, respondent)
    assert run.probes_asked == {}

    llm = FakeLLM(_record("Line lead"), _follow_up("What does that involve?"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)
    assert "ask_follow_up" in llm.offered[-1]


async def test_rewind_takes_back_only_the_last_answer(session, respondent, author):
    """One step, not a reset. Earlier answers and the transcript that produced them stay."""
    template = await _publish(
        session,
        author,
        QuestionInput(text="What's your role?", answer_type=AnswerType.short_text),
        QuestionInput(text="Which site?", answer_type=AnswerType.short_text),
        QuestionInput(text="Rate your onboarding", answer_type=AnswerType.rating),
    )
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(template.id, respondent)

    run = await ConductEngine(session, llm=FakeLLM(_record("Line lead"))).handle_message(
        run.id, "line lead", respondent
    )
    run = await ConductEngine(session, llm=FakeLLM(_record("Derby"))).handle_message(
        run.id, "derby", respondent
    )
    assert run.current_question_index == 2

    run = await ConductEngine(session, llm=FakeLLM()).rewind_last_answer(run.id, respondent)

    assert run.current_question_index == 1
    assert [a.value for a in run.answers] == [{"text": "Line lead"}]
    assert [m.role for m in run.messages] == [
        MessageRole.assistant,
        MessageRole.user,
        MessageRole.assistant,
    ]


async def test_rewind_lets_a_skipped_question_come_back(session, respondent, author):
    """Why one step is the safe number. The questions after the rewound one hold no
    answers, so re-deciding their visibility is just `_advance` doing its usual job: the
    condition is read again from the answer the respondent gives the second time."""
    template = await _publish(
        session,
        author,
        QuestionInput(text="Have you been trained?", answer_type=AnswerType.yes_no),
        QuestionInput(
            text="What were you trained on?",
            answer_type=AnswerType.long_text,
            show_when={"question": 0, "op": "is", "value": "yes"},
        ),
        QuestionInput(text="Rate the training", answer_type=AnswerType.rating),
    )
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(template.id, respondent)

    run = await ConductEngine(session, llm=FakeLLM(_record(False))).handle_message(
        run.id, "no", respondent
    )
    assert run.current_question_index == 2  # "no" hid the middle question

    run = await ConductEngine(session, llm=FakeLLM()).rewind_last_answer(run.id, respondent)
    assert run.current_question_index == 0

    run = await ConductEngine(session, llm=FakeLLM(_record(True))).handle_message(
        run.id, "yes", respondent
    )
    assert run.current_question_index == 1  # and "yes" brings it back


async def test_rewind_is_refused_once_the_run_is_finished(session, respondent, published):
    """A completed run is sealed. The author may already have read it, so it must not
    change underneath them."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("Line lead"), _move_on("Rate your onboarding."))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)
    run = await ConductEngine(session, llm=FakeLLM(_record(4))).handle_message(
        run.id, "4", respondent
    )
    assert run.status is RunStatus.completed

    with pytest.raises(ConflictError, match="finished"):
        await ConductEngine(session, llm=FakeLLM()).rewind_last_answer(run.id, respondent)


async def test_rewind_is_refused_before_anything_is_answered(session, respondent, published):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    with pytest.raises(ConflictError, match="Nothing has been answered"):
        await ConductEngine(session, llm=FakeLLM()).rewind_last_answer(run.id, respondent)


async def test_rewind_is_refused_to_another_respondent(
    session, respondent, other_respondent, published
):
    """The same ownership gate as reading the run: a rewind is a write to someone's
    answers, and must not be reachable by guessing a run id."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    llm = FakeLLM(_record("Line lead"), _move_on("Rate your onboarding."))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    with pytest.raises(ForbiddenError):
        await ConductEngine(session, llm=FakeLLM()).rewind_last_answer(run.id, other_respondent)


# ------------------------------------------------------- what the turn cost the run


class _MeteredLLM(FakeLLM):
    """A FakeLLM that also books its calls to the ledger, as the real client does.

    Subclassed rather than mocked because the wiring under test is precisely that the
    engine's accumulator is active *while* the client runs: a stub that recorded outside
    the block would pass while the real thing recorded nothing.
    """

    async def tool_turn(self, **kwargs):
        turn = await super().tool_turn(**kwargs)
        ledger.record(
            tier=4,
            model="llama3.2:3b",
            op="tool_turn",
            usage={"prompt_tokens": 100, "completion_tokens": 10},
            latency_ms=1000,
            status=200,
        )
        return turn


async def test_a_turns_model_spend_lands_on_the_run(session, respondent, published):
    """Answering costs tokens, and the run is where that is answerable per survey."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    assert run.llm_calls == 0

    llm = _MeteredLLM(_record("Line lead"), _move_on("Thanks."))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    # Two model calls this turn: the record, then the move-on decision.
    assert run.llm_calls == 2
    assert run.llm_prompt_tokens == 200
    assert run.llm_completion_tokens == 20
    assert run.llm_cost_usd > 0  # tier 4 is local, so priced by the clock


async def test_spend_accumulates_across_turns_rather_than_being_replaced(
    session, respondent, published
):
    """A run's cost is the whole conversation's, not the last message's."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = _MeteredLLM(_record("Line lead"), _follow_up("What does that involve?"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)
    after_first = run.llm_calls

    llm = _MeteredLLM(_record("Running the line"), _move_on("Thanks."))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "running it", respondent)

    assert run.llm_calls > after_first
    assert run.llm_prompt_tokens == 100 * run.llm_calls


async def test_rewind_refunds_the_next_questions_budgets_too(session, respondent, author):
    """The deleted turns can have spent probes or replies on the NEXT question, since
    probing is not gated on an answer existing and a confused respondent's questions
    cost replies. A budget charged for conversation that no longer exists left the
    model with record or flag_unanswerable as its only legal moves on the way back."""
    template = await _publish(
        session,
        author,
        QuestionInput(text="What's your role?", answer_type=AnswerType.short_text),
        QuestionInput(
            text="Which systems do you use?",
            answer_type=AnswerType.short_text,
            allow_follow_ups=True,
        ),
    )
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(template.id, respondent)

    run = await ConductEngine(session, llm=FakeLLM(_record("Line lead"))).handle_message(
        run.id, "line lead", respondent
    )
    assert run.current_question_index == 1

    # On q1 the respondent asks what the question means (a reply), and the model probes
    # for an answer the reply did not contain (a follow-up): both budgets are spent.
    llm = FakeLLM(_reply("I mean software you use daily. Which systems do you use?"))
    run = await ConductEngine(session, llm=llm).handle_message(
        run.id, "what do you mean?", respondent
    )
    llm = FakeLLM(_follow_up("Could you name the main one?"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "a few things", respondent)
    assert run.probes_asked != {}

    run = await ConductEngine(session, llm=FakeLLM()).rewind_last_answer(run.id, respondent)

    # Q1's spend belonged to deleted conversation, so it is refunded with the rewind.
    assert run.current_question_index == 0
    assert run.probes_asked == {}


async def test_rewind_keeps_the_budgets_of_questions_that_keep_their_transcript(
    session, respondent, author
):
    """Only the deleted turns are refunded. An earlier question's probes still happened."""
    template = await _publish(
        session,
        author,
        QuestionInput(
            text="What's your role?", answer_type=AnswerType.short_text, allow_follow_ups=True
        ),
        QuestionInput(text="Which site?", answer_type=AnswerType.short_text),
        QuestionInput(text="Rate your onboarding", answer_type=AnswerType.rating),
    )
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(template.id, respondent)

    llm = FakeLLM(_record("Line lead"), _follow_up("What does that involve?"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)
    llm = FakeLLM(_record("Running the line"), _move_on())
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "running it", respondent)
    spent_on_q0 = dict(run.probes_asked)
    assert spent_on_q0 != {}

    run = await ConductEngine(session, llm=FakeLLM(_record("Derby"))).handle_message(
        run.id, "derby", respondent
    )
    run = await ConductEngine(session, llm=FakeLLM()).rewind_last_answer(run.id, respondent)

    assert run.current_question_index == 1
    assert run.probes_asked == spent_on_q0  # q0's transcript survives, so does its spend


async def test_a_follow_up_on_a_write_in_select_records_prose_as_text(session, respondent, author):
    """allow_other accepts ANY string as a write-in, which made the follow-up prose path
    unreachable: a description of a problem was stored as an option the respondent
    supposedly picked, indistinguishable from a write-in choice in the export."""
    template = await _publish(
        session,
        author,
        QuestionInput(
            text="Which system do you use most?",
            answer_type=AnswerType.single_select,
            options=["Scanner", "Terminal"],
            allow_other=True,
            allow_follow_ups=True,
        ),
    )
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(template.id, respondent)

    llm = FakeLLM(_record("Scanner"), _follow_up("Any issues with it?"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "the scanner", respondent)

    llm = FakeLLM(_record("It drops its connection every few hours."), _move_on())
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "it drops out", respondent)

    follow_ups = [a for a in run.answers if a.kind is AnswerKind.follow_up]
    assert follow_ups[0].value == {"text": "It drops its connection every few hours."}


async def test_a_follow_up_naming_an_actual_option_stays_structured_despite_allow_other(
    session, respondent, author
):
    """The other half: "which of those did you mean?" answered with an option should
    record the option, even on a question that also accepts write-ins."""
    template = await _publish(
        session,
        author,
        QuestionInput(
            text="Which system do you use most?",
            answer_type=AnswerType.single_select,
            options=["Scanner", "Terminal"],
            allow_other=True,
            allow_follow_ups=True,
        ),
    )
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(template.id, respondent)

    llm = FakeLLM(_record("Scanner"), _follow_up("Just to check, the handheld one?"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "the scanner", respondent)

    llm = FakeLLM(_record("Terminal"), _move_on())
    run = await ConductEngine(session, llm=llm).handle_message(
        run.id, "no, the terminal actually", respondent
    )

    follow_ups = [a for a in run.answers if a.kind is AnswerKind.follow_up]
    assert follow_ups[0].value == {"option": "Terminal"}
