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
    PROMPT_VERSION,
    TRANSCRIPT_WINDOW,
    ConductEngine,
    _transcript,
)
from app.conduct.repository import RunRepository
from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.i18n import translate
from app.llm import ledger
from app.llm.client import LLMError, NoToolCallError, ToolTurn
from app.pii import PIIInMessageError
from app.runs.enums import AnswerKind, MessageRole, RunStatus
from app.runs.models import RunMessage, SurveyRun
from app.templates.enums import AnswerType, FollowUpPolicy
from app.templates.schemas import QuestionInput, TemplateCreate
from app.templates.service import TemplateService
from tests.builders import update_of
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


async def test_the_engine_claims_the_nudged_retry_from_the_failover_chain(
    session, respondent, published
):
    """The engine is the one caller that answers NoToolCallError itself, so it is the
    one caller allowed to stop a chatty turn cascading. Asserted at the boundary rather
    than trusted, because the flag defaulting the wrong way is invisible: every test
    passes either way and only a live chain shows the difference."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("Line lead"), _move_on("Thanks."))
    await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    assert llm.cascade_flags == [False, False]


async def test_progress_does_not_count_the_current_question_twice_while_probing(
    session, respondent, published
):
    """`published` has two questions and q0 permits probing. Once q0's answer is
    recorded the engine loops without advancing, so `answered` already counts q0 while
    remaining_possible counts inclusively from the unmoved index and counts it again.
    The respondent read "1 of 3" on a two-question survey, and the denominator shrank to
    2 when the probe finished, which reads as the survey growing shorter as you answer.
    """
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("Line lead"), _follow_up("What does that involve?"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    reader = ConductEngine(session, llm=FakeLLM())
    questions = await reader.questions(run)
    assert reader.probing(run, questions) is True
    assert reader.progress(run, questions) == (1, 2)


async def test_probing_is_false_once_the_engine_has_moved_on(session, respondent, published):
    """The other edge of the same predicate: after the engine advances, the question the
    respondent is looking at is scripted again and its typed controls are correct."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("Line lead"), _move_on("Thanks. How was onboarding?"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    reader = ConductEngine(session, llm=FakeLLM())
    questions = await reader.questions(run)
    assert reader.probing(run, questions) is False
    assert reader.progress(run, questions) == (1, 2)


async def test_a_tier_that_chats_twice_is_allowed_to_fall_to_the_next_one(
    session, respondent, published
):
    """The nudge is for a tier that went off-script once. A tier that answers the same
    way twice is not chatting, it is structurally unable to answer: a model ignoring
    parallel_tool_calls returns two tool calls on every turn, and refusing to cascade
    would 503 every respondent message with healthy tiers below never contacted."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(NoToolCallError("chatted"), _record("Line lead"), _move_on("Thanks."))
    await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    # First attempt holds the tier for the nudge; the nudged retry may cascade.
    assert llm.cascade_flags[:2] == [False, True]


async def test_engine_withholds_follow_up_once_the_cap_is_spent(session, respondent, published):
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    # Answer, then probe, as many times as the cap allows. Driven by MAX_FOLLOW_UPS
    # rather than a fixed count, because a test that hardcodes "twice" while asserting
    # against the constant only passes while the constant happens to be two.
    for i in range(MAX_FOLLOW_UPS):
        reply = f"Probe {i + 1}, what does that involve?"
        llm = FakeLLM(_record("Line lead"), _follow_up(reply))
        run = await ConductEngine(session, llm=llm).handle_message(run.id, "…", respondent)
        assert run.current_question_index == 0  # a follow-up must not advance the survey
        assert run.messages[-1].content == reply

    # The next answer lands with the cap spent, so ask_follow_up is no longer offered.
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

    # Reply evasively; the model probes again without recording anything, until the
    # budget is gone. One probe is already spent above, hence the minus one.
    for i in range(MAX_FOLLOW_UPS - 1):
        again = FakeLLM(_follow_up(f"Could you say a bit more? ({i + 1})"))
        run = await ConductEngine(session, llm=again).handle_message(
            run.id, "dunno really", respondent
        )

    assert run.probes_asked == {published_question_id(run): MAX_FOLLOW_UPS}
    assert not [a for a in run.answers if a.kind is AnswerKind.follow_up]  # nothing recorded

    # The budget is now spent even though no follow-up answer exists.
    over_budget = FakeLLM(_follow_up("And anything else?"))
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=over_budget).handle_message(
            run.id, "still dunno", respondent
        )
    assert "ask_follow_up" not in over_budget.offered[-1]


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
    # Rejected, retried, then offered the chance to ask a follow-up instead of failing.
    # A model that returns the same unusable call all three times has run out of things
    # to try, and the turn fails rather than pretending otherwise.
    assert llm.calls == 3


async def test_unknown_tool_name_is_rejected(session, respondent, published):
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    invented = ToolTurn(text="", tool_name="skip_survey", tool_input={})
    llm = FakeLLM(invented)
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=llm).handle_message(run.id, "hello", respondent)
    assert llm.calls == 3  # rejected, retried, offered a follow-up, still unusable


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
        update_of(
            published,
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
    assert llm.calls == 3  # rejected, retried, offered a follow-up, still unusable
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
        run.id, "the scanner drops its connection every few hours", respondent
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
    # Their own words, so the record is grounded and the probe is resolved. Answering a
    # probe with "…" and then moving on is no longer a path the engine offers: a question
    # it asked has to be recorded or flagged, never left hanging.
    await ConductEngine(session, llm=probe).handle_message(
        run.id, "because the scanner drops out", respondent
    )

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
            follow_up_policy=FollowUpPolicy.when_unclear,
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
            text="What's your role?",
            answer_type=AnswerType.short_text,
            follow_up_policy=FollowUpPolicy.when_unclear,
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
            follow_up_policy=FollowUpPolicy.when_unclear,
        ),
    )
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(template.id, respondent)

    llm = FakeLLM(_record("Scanner"), _follow_up("Any issues with it?"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "the scanner", respondent)

    llm = FakeLLM(_record("It drops its connection every few hours."), _move_on())
    run = await ConductEngine(session, llm=llm).handle_message(
        run.id, "it drops its connection every few hours", respondent
    )

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
            follow_up_policy=FollowUpPolicy.when_unclear,
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


async def test_a_probe_banks_the_answer_the_reply_already_held(session, respondent, published):
    """The live run this exists for.

    Asked what challenges they faced, the respondent said "tempereture". The model probed
    instead of recording, the respondent's reply to the probe was about the reading rather
    than the challenge, and the model then flagged the question unanswerable. Nothing had
    been recorded, so that flag landed on the question itself: a real answer replaced by a
    note saying none was given. Banking it before the probe is asked is what survives a
    probe that goes nowhere.
    """
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    probe = FakeLLM(_follow_up("How is temperature a challenge?", answer_so_far="tempereture"))
    run = await ConductEngine(session, llm=probe).handle_message(run.id, "tempereture", respondent)

    banked = [a for a in run.answers if a.kind is AnswerKind.scripted]
    assert [a.value for a in banked] == [{"text": "tempereture"}]
    assert run.current_question_index == 0  # banked, not advanced: the probe still stands
    assert run.messages[-1].content == "How is temperature a challenge?"

    # The probe goes nowhere and the model gives up on it. The banked answer is untouched,
    # and the flag attaches to the probe rather than to the question.
    giving_up = FakeLLM(_decline("did not answer the question about challenges"))
    run = await ConductEngine(session, llm=giving_up).handle_message(
        run.id, "was around 6c", respondent
    )

    scripted = [a for a in run.answers if a.kind is AnswerKind.scripted]
    assert [a.value for a in scripted] == [{"text": "tempereture"}]
    assert [a.value for a in run.answers if a.kind is AnswerKind.follow_up] == [
        {"unanswerable": "did not answer the question about challenges"}
    ]


async def test_a_probe_must_say_whether_the_reply_held_an_answer(session, respondent, published):
    """Required and nullable, not optional. A model that has an answer must not be able to
    walk past the field without saying so, which is how the answer went missing."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    silent = FakeLLM(
        ToolTurn(text="", tool_name="ask_follow_up", tool_input={"follow_up_text": "Say more?"}),
        ToolTurn(text="", tool_name="ask_follow_up", tool_input={"follow_up_text": "Say more?"}),
    )
    with pytest.raises(LLMError, match="answer_so_far"):
        await ConductEngine(session, llm=silent).handle_message(run.id, "tempereture", respondent)


async def test_a_banked_answer_is_held_to_the_recording_rules(session, respondent, published):
    """Banking is recording, so it answers to the same gates. Otherwise ask_follow_up is
    a second door into the answers table with no grounding check on it, and the fabricated
    free text the 0.6 gate exists to catch walks straight through."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    invented = FakeLLM(
        _follow_up("Which line?", answer_so_far="Senior maintenance engineer, night shift"),
        _follow_up("Which line?", answer_so_far="Senior maintenance engineer, night shift"),
    )
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=invented).handle_message(
            run.id, "dunno really", respondent
        )
    assert not run.answers


async def test_banking_is_not_offered_once_the_answer_is_in(session, respondent, published):
    """A second scripted answer is not a thing that exists. Once one is recorded the probe
    tool goes back to its old shape, and the model records the probe's answer as a
    follow-up in the normal way."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    # Two turns: recording does not advance while the question still permits probing, so
    # the engine loops and the model decides again with the answer now in.
    first = FakeLLM(_record("Line lead"), _move_on())
    run = await ConductEngine(session, llm=first).handle_message(run.id, "line lead", respondent)

    probing = [t for t in first.tools_seen[-1] if t["name"] == "ask_follow_up"]
    assert probing, "the question permits probing, so the tool must still be offered"
    assert "answer_so_far" not in probing[0]["input_schema"]["properties"]


async def _published_with_setting(session, author, setting: str | None):
    """A one-question survey whose author has described the workplace."""
    svc = TemplateService(session)
    template = await svc.create_draft(
        TemplateCreate(
            title="Compliance check",
            setting=setting,
            questions=[
                QuestionInput(
                    text="What challenges do you face maintaining compliance?",
                    answer_type=AnswerType.short_text,
                    follow_up_policy=FollowUpPolicy.when_unclear,
                )
            ],
        ),
        author,
    )
    await svc.publish(template.id, author)
    return template


_PLANT = (
    "Chilled fish processing plant. Fresh fish is held on ice at 0 to 2 degrees; "
    "anything above that is a chill-chain problem. Respondents are line leaders."
)


async def test_the_setting_reaches_the_interviewer(session, author, respondent):
    """Without it a reply in the trade's own vocabulary reads as evasive. A respondent
    answering "temperature" and then a reading in degrees is being specific."""
    published = await _published_with_setting(session, author, _PLANT)
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("temperature"), _move_on())
    await ConductEngine(session, llm=llm).handle_message(run.id, "tempereture", respondent)

    briefing = llm.briefings[0]
    assert "THE SETTING" in briefing
    assert "held on ice at 0 to 2 degrees" in briefing


async def test_a_survey_with_no_setting_briefs_without_one(session, author, respondent):
    """Most surveys have none, and an empty heading announcing a setting that follows and
    then does not is worse than silence."""
    published = await _published_with_setting(session, author, None)
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("paperwork"), _move_on())
    await ConductEngine(session, llm=llm).handle_message(run.id, "paperwork", respondent)

    assert "THE SETTING" not in llm.briefings[0]


async def test_a_blank_setting_is_the_same_as_none(session, author, respondent):
    """An author who cleared the box has described nothing. Whitespace is not a setting."""
    published = await _published_with_setting(session, author, "   ")
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("paperwork"), _move_on())
    await ConductEngine(session, llm=llm).handle_message(run.id, "paperwork", respondent)

    assert "THE SETTING" not in llm.briefings[0]


async def test_the_setting_is_never_said_to_the_respondent(session, author, respondent):
    """It is written for the interviewer. The engine's own words are the opening line and
    the closing one, and neither may carry the author's private notes into the chat."""
    published = await _published_with_setting(session, author, _PLANT)
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("temperature"), _move_on())
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "tempereture", respondent)

    spoken = " ".join(m.content for m in run.messages)
    assert "held on ice" not in spoken
    assert "line leaders" not in spoken


async def test_the_setting_is_frozen_at_publish(session, author, respondent):
    """A run is conducted against what was published. An author rewriting the draft
    mid-study must not change how answers already being given are read."""
    published = await _published_with_setting(session, author, _PLANT)
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    svc = TemplateService(session)
    template = await svc.get_draft(published.id, author)
    await svc.update_draft(
        published.id, update_of(template, setting="Completely different workplace."), author
    )

    llm = FakeLLM(_record("temperature"), _move_on())
    await ConductEngine(session, llm=llm).handle_message(run.id, "tempereture", respondent)

    briefing = llm.briefings[0]
    assert "held on ice at 0 to 2 degrees" in briefing
    assert "Completely different workplace" not in briefing


_PLANT_CONFIG = (
    "Chilled fish processing plant, BRCGS certified. Fresh fish is held on ice at 0 to 2 "
    "degrees; above that is a chill-chain problem. Respondents are line leaders."
)


@pytest.fixture
def deployment_setting(monkeypatch):
    """The workplace as deployment config, the way a real install supplies it."""
    from app.config import get_settings

    monkeypatch.setenv("SURVEY_SETTING", _PLANT_CONFIG)
    get_settings.cache_clear()
    yield _PLANT_CONFIG
    monkeypatch.delenv("SURVEY_SETTING", raising=False)
    get_settings.cache_clear()


async def test_the_deployment_setting_reaches_the_interviewer(
    session, author, respondent, deployment_setting
):
    """The plant does not change between surveys, so asking every author to retype it is
    how it ends up wrong on half of them. Configured once, it reaches every survey
    published here without an author writing anything."""
    published = await _published_with_setting(session, author, None)
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("temperature"), _move_on())
    await ConductEngine(session, llm=llm).handle_message(run.id, "tempereture", respondent)

    briefing = llm.briefings[0]
    assert "THE SETTING" in briefing
    assert "held on ice at 0 to 2" in briefing


async def test_a_surveys_own_setting_beats_the_deployments(
    session, author, respondent, deployment_setting
):
    """The deployment default answers "most surveys"; it does not overrule the author who
    took the trouble to describe something different."""
    published = await _published_with_setting(session, author, "A dry goods warehouse.")
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("paperwork"), _move_on())
    await ConductEngine(session, llm=llm).handle_message(run.id, "paperwork", respondent)

    briefing = llm.briefings[0]
    assert "A dry goods warehouse." in briefing
    assert "held on ice" not in briefing


async def test_the_deployment_setting_is_frozen_at_publish(
    session, author, respondent, monkeypatch
):
    """Editing the deployment's description must not change how answers already being
    given are read, for the same reason editing the draft does not."""
    from app.config import get_settings

    monkeypatch.setenv("SURVEY_SETTING", _PLANT_CONFIG)
    get_settings.cache_clear()
    published = await _published_with_setting(session, author, None)
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)

    monkeypatch.setenv("SURVEY_SETTING", "Somewhere else entirely.")
    get_settings.cache_clear()

    llm = FakeLLM(_record("temperature"), _move_on())
    await ConductEngine(session, llm=llm).handle_message(run.id, "tempereture", respondent)

    briefing = llm.briefings[0]
    assert "held on ice at 0 to 2" in briefing
    assert "Somewhere else" not in briefing
    monkeypatch.delenv("SURVEY_SETTING", raising=False)
    get_settings.cache_clear()


async def test_the_deployment_setting_is_never_said_to_the_respondent(
    session, author, respondent, deployment_setting
):
    """It is written for the interviewer. Asserted rather than assumed, because this is
    the one that matters: the plant's own description is not a thing to read out to the
    people working in it."""
    published = await _published_with_setting(session, author, None)
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("temperature"), _move_on())
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "tempereture", respondent)

    spoken = " ".join(m.content for m in run.messages)
    assert "BRCGS" not in spoken
    assert "held on ice" not in spoken


async def test_no_deployment_setting_means_no_setting(session, author, respondent):
    """The common case for anyone who is not this plant. An empty config is not a setting,
    and an empty heading announcing one that follows and then does not is worse."""
    published = await _published_with_setting(session, author, None)
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("paperwork"), _move_on())
    await ConductEngine(session, llm=llm).handle_message(run.id, "paperwork", respondent)

    assert "THE SETTING" not in llm.briefings[0]


# --- always_once: the engine owns whether a probe happens, not only how many -----------


async def _published_always_once(session, author, required: bool = True):
    """One question the author marked as always taking a follow-up, then a plain one."""
    return await _publish(
        session,
        author,
        QuestionInput(
            text="Has the heat affected your work or your health?",
            answer_type=AnswerType.long_text,
            required=required,
            follow_up_policy=FollowUpPolicy.always_once,
        ),
        QuestionInput(text="Which shift do you work?", answer_type=AnswerType.short_text),
    )


async def test_always_once_withholds_the_ways_past_the_question(session, respondent, author):
    """The fault this exists for. `allow_follow_ups` granted permission, the prompt calls
    the budget a ceiling, and a live survey with four probe-enabled questions asked eight
    people ninety-odd turns and never followed up once. Permission is not intent, so on
    `always_once` the engine stops offering the ways past."""
    template = await _published_always_once(session, author)
    run = await ConductEngine(session, llm=FakeLLM()).start_run(template.id, respondent)

    llm = FakeLLM(_follow_up("What happened, and when?", answer_so_far="yes, headaches"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "yes, headaches", respondent)

    offered = llm.offered[0]
    assert "record_answer" not in offered
    assert "move_on" not in offered
    assert "ask_follow_up" in offered
    # Never cornered: declining is available on the forced turn like any other.
    assert "flag_unanswerable" in offered
    assert run.current_question_index == 0


async def test_the_forced_probe_banks_the_answer_rather_than_losing_it(session, respondent, author):
    """Withholding `record_answer` must not cost the answer they already gave.
    `ask_follow_up` carries `answer_so_far` for exactly this, so the scripted answer and
    the probe are one call and no turn is spent."""
    template = await _published_always_once(session, author)
    run = await ConductEngine(session, llm=FakeLLM()).start_run(template.id, respondent)

    llm = FakeLLM(_follow_up("What happened, and when?", answer_so_far="yes, headaches"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "yes, headaches", respondent)

    scripted = [a for a in run.answers if a.kind is AnswerKind.scripted]
    assert [a.value for a in scripted] == [{"text": "yes, headaches"}]


async def test_the_obligation_lapses_after_one_probe(session, respondent, author):
    """One follow-up, not one per turn. The budget is spent when the probe is issued, so
    the rest of it goes back to the model's judgement and the run always terminates."""
    template = await _published_always_once(session, author)
    run = await ConductEngine(session, llm=FakeLLM()).start_run(template.id, respondent)
    first = FakeLLM(_follow_up("What happened?", answer_so_far="yes, headaches"))
    run = await ConductEngine(session, llm=first).handle_message(
        run.id, "yes, headaches", respondent
    )

    second = FakeLLM(_record("most afternoons in July"), _move_on())
    run = await ConductEngine(session, llm=second).handle_message(
        run.id, "most afternoons in July", respondent
    )

    assert "record_answer" in second.offered[0]
    assert "move_on" in second.offered[-1]
    assert [a.kind for a in run.answers] == [AnswerKind.scripted, AnswerKind.follow_up]
    assert run.current_question_index == 1


async def test_a_declined_forced_probe_still_moves_the_survey_on(session, respondent, author):
    """The escape hatch, proven rather than assumed. A respondent who will not elaborate
    must not be held on the question by an author's setting."""
    template = await _published_always_once(session, author)
    run = await ConductEngine(session, llm=FakeLLM()).start_run(template.id, respondent)
    run = await ConductEngine(
        session, llm=FakeLLM(_follow_up("What happened?", answer_so_far="yes, headaches"))
    ).handle_message(run.id, "yes, headaches", respondent)

    declining = FakeLLM(
        ToolTurn(
            text="",
            tool_name="flag_unanswerable",
            tool_input={"question_id": "x", "reason": "would rather not say"},
        )
    )
    run = await ConductEngine(session, llm=declining).handle_message(
        run.id, "rather not", respondent
    )

    assert run.current_question_index == 1


async def test_an_optional_question_is_never_forced(session, respondent, author):
    """`conduct_v7.md` already holds that pressing someone who has just deflected is how
    invented answers get recorded. An optional question is a courtesy by definition, so
    the author's intent stops at the respondent who said they cannot help."""
    template = await _published_always_once(session, author, required=False)
    run = await ConductEngine(session, llm=FakeLLM()).start_run(template.id, respondent)

    llm = FakeLLM(_record("no, it has been fine"), _move_on())
    run = await ConductEngine(session, llm=llm).handle_message(
        run.id, "no, it has been fine", respondent
    )

    assert "record_answer" in llm.offered[0]
    assert run.current_question_index == 1


async def test_the_briefing_says_why_record_answer_is_missing(session, respondent, author):
    """Enforced by the tool list and said out loud as well: a model that finds
    `record_answer` gone and is told nothing spends its retry guessing why."""
    template = await _published_always_once(session, author)
    run = await ConductEngine(session, llm=FakeLLM()).start_run(template.id, respondent)

    llm = FakeLLM(_follow_up("What happened?", answer_so_far="yes, headaches"))
    await ConductEngine(session, llm=llm).handle_message(run.id, "yes, headaches", respondent)

    assert "ALWAYS TAKES ONE FOLLOW-UP" in llm.briefings[0]


async def test_a_probe_that_was_answered_cannot_be_walked_away_from(session, respondent, author):
    """A live run asked "what happens after a stoppage is logged?", forced because the
    author marked it always_once, got a paragraph about nobody ever coming back to ask,
    and moved on without recording a word of it. The force guarantees the question is
    asked; nothing guaranteed the answer was kept."""
    template = await _published_always_once(session, author)
    run = await ConductEngine(session, llm=FakeLLM()).start_run(template.id, respondent)
    run = await ConductEngine(
        session, llm=FakeLLM(_follow_up("What happened?", answer_so_far="yes, headaches"))
    ).handle_message(run.id, "yes, headaches", respondent)

    answering = FakeLLM(_record("most afternoons, near the ovens"), _move_on())
    run = await ConductEngine(session, llm=answering).handle_message(
        run.id, "most afternoons, near the ovens", respondent
    )

    # Withheld while the probe was outstanding, offered again once it was recorded.
    assert "move_on" not in answering.offered[0]
    assert "record_answer" in answering.offered[0]
    assert "flag_unanswerable" in answering.offered[0]
    assert "move_on" in answering.offered[-1]
    follow_ups = [a for a in run.answers if a.kind is AnswerKind.follow_up]
    assert [a.value for a in follow_ups] == [{"text": "most afternoons, near the ovens"}]


async def test_declining_a_probe_resolves_it_too(session, respondent, author):
    """The other way out, and it must stay open: a respondent who will not elaborate is
    not a reason to hold the survey. "Asked and declined" is a finding; silence is
    indistinguishable from never having asked."""
    template = await _published_always_once(session, author)
    run = await ConductEngine(session, llm=FakeLLM()).start_run(template.id, respondent)
    run = await ConductEngine(
        session, llm=FakeLLM(_follow_up("What happened?", answer_so_far="yes, headaches"))
    ).handle_message(run.id, "yes, headaches", respondent)

    declining = FakeLLM(
        ToolTurn(
            text="",
            tool_name="flag_unanswerable",
            tool_input={"question_id": "x", "reason": "would rather not go into it"},
        )
    )
    run = await ConductEngine(session, llm=declining).handle_message(
        run.id, "rather not", respondent
    )

    declined = [a for a in run.answers if a.kind is AnswerKind.follow_up]
    assert declined and "unanswerable" in declined[0].value
    assert run.current_question_index == 1


async def test_an_unprobed_question_can_still_be_moved_on_from(session, respondent, author):
    """The rule is about a probe left hanging, not about probing. A question nobody
    probed must still cost exactly one exchange."""
    template = await _published_always_once(session, author, required=False)
    run = await ConductEngine(session, llm=FakeLLM()).start_run(template.id, respondent)

    llm = FakeLLM(_record("no, it has been fine"), _move_on())
    run = await ConductEngine(session, llm=llm).handle_message(
        run.id, "no, it has been fine", respondent
    )

    assert "move_on" in llm.offered[-1]
    assert run.current_question_index == 1


# ------------------------------------------------------------------ provenance


async def test_an_assistant_turn_records_the_prompt_version_that_produced_it(
    session, respondent, published
):
    """Which authored text wrote this line. Without it a prompt bump leaves every stored
    run unattributable: the transcript reads the same before and after, and the version
    that regressed a conversation cannot be identified from the conversation."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("Line lead"), _move_on("Thanks."))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    assert run.messages[-1].prompt_version == PROMPT_VERSION


async def test_the_respondents_own_words_carry_no_provenance(session, respondent, published):
    """Null rather than the engine's prompt version. They wrote it; no model did, and a
    stamp here would claim otherwise."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("Line lead"), _move_on("Thanks."))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    said = [m for m in run.messages if m.role is MessageRole.user]
    assert said and all(m.prompt_version is None and m.model is None for m in said)


async def test_the_opening_line_carries_no_provenance(session, respondent, published):
    """The engine composes it from the version definition without asking a model, so it
    has no prompt version and no tier. Recorded as unknown because it is."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)

    opening = run.messages[0]
    assert opening.role is MessageRole.assistant
    assert (opening.prompt_version, opening.model, opening.tier) == (None, None, None)


async def test_an_assistant_turn_records_the_tier_that_actually_answered(
    session, respondent, published
):
    """Read back from the measured spend rather than from settings, so it names the tier
    that answered instead of the one that was configured. The two part company on any
    turn that failed over, and the message about to be stored holds the words of the one
    that answered."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("Line lead"), _move_on("Thanks."), serves_as=(2, "llama-70b"))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    assert (run.messages[-1].model, run.messages[-1].tier) == ("llama-70b", 2)


# ------------------------------------------------------- contact details never get in


async def test_a_message_carrying_an_email_address_is_refused(session, respondent, published):
    """Refused before the append and before the model call, which is the whole ordering.

    A check after the call would have handed the address to a hosted provider already, and
    one after the append would have written it into a transcript the author reads. Nothing
    is stored, nothing is sent, and the fake is left holding a turn nobody asked for.
    """
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    before = len(run.messages)

    llm = FakeLLM(_record("Line lead"), _move_on())
    with pytest.raises(PIIInMessageError):
        await ConductEngine(session, llm=llm).handle_message(
            run.id, "I'm the line lead, ravi@example.com", respondent
        )

    assert llm.calls == 0  # no model call, so the refusal costs the run nothing
    reloaded = await ConductEngine(session, llm=FakeLLM()).load(run.id, respondent)
    assert len(reloaded.messages) == before
    assert not any("ravi@example.com" in m.content for m in reloaded.messages)


async def test_the_refusal_is_written_in_the_runs_language(session, respondent, published):
    """The handler renders an AppError's message verbatim, so a respondent-facing
    sentence has to be translated where it is raised. The engine is the only place that
    knows which language this run is being conducted in."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent, language="es")

    with pytest.raises(PIIInMessageError) as raised:
        await ConductEngine(session, llm=FakeLLM()).handle_message(
            run.id, "escríbeme a ravi@example.com", respondent
        )

    assert raised.value.message == translate("pii_in_message", "es")
    assert raised.value.message != translate("pii_in_message", "en")


async def test_the_refusal_does_not_repeat_the_value_it_objected_to(session, respondent, published):
    """A message quoting the number it refused has just written that number into a second
    place: the API response, and from there whatever logs it."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    with pytest.raises(PIIInMessageError) as raised:
        await ConductEngine(session, llm=FakeLLM()).handle_message(
            run.id, "ring me on 07700 900123", respondent
        )

    assert "07700" not in raised.value.message
    assert "900123" not in raised.value.message


async def test_an_answer_about_a_batch_code_is_not_refused(session, respondent, published):
    """The other direction, at the engine rather than in isolation. This survey asks a
    fish plant about batch codes; a gate that refused one would refuse the answer the
    survey exists to collect."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    llm = FakeLLM(_record("Line lead"), _move_on("Thanks."))
    run = await ConductEngine(session, llm=llm).handle_message(
        run.id, "line lead, batch 4021998745 was the warm one", respondent
    )

    assert llm.calls == 2
    assert run.current_question_index == 1


# ------------------------------------------------------------------ erasure


async def test_a_respondent_can_erase_their_own_run(session, respondent, published):
    """The other half of the 10 Aug agreement: no names on answers, and erasure on
    request. Answers and transcript go with the run, which the cascades already handle."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    llm = FakeLLM(_record("Line lead"), _move_on("Thanks."))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)
    assert run.answers

    await ConductEngine(session, llm=FakeLLM()).delete_run(run.id, respondent)

    with pytest.raises(NotFoundError):
        await ConductEngine(session, llm=FakeLLM()).load(run.id, respondent)


async def test_erasure_takes_the_answers_and_the_transcript_with_it(
    engine, session, respondent, published
):
    """Checked against the tables rather than through the engine, because "the run is
    gone" and "what the run held is gone" are different claims and only the second one is
    the promise. Orphaned answers would still be the respondent's words, still readable,
    and no longer attached to anything that could be deleted again."""
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.runs.models import Answer

    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    llm = FakeLLM(_record("Line lead"), _move_on("Thanks."))
    run = await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)
    await session.commit()

    await ConductEngine(session, llm=FakeLLM()).delete_run(run.id, respondent)

    async with AsyncSession(engine, expire_on_commit=False) as fresh:
        answers = (await fresh.execute(select(Answer).where(Answer.run_id == run.id))).all()
        messages = (
            await fresh.execute(select(RunMessage).where(RunMessage.run_id == run.id))
        ).all()
    assert answers == []
    assert messages == []


async def test_a_completed_run_can_still_be_erased(session, respondent, published):
    """Deliberately unlike rewind, which refuses a finished run because the author may
    have read it. Here that is the reason someone asks, not a reason to refuse them: a
    finished run is the only kind worth erasing."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)
    answered = FakeLLM(_record("Line lead"), _move_on())
    run = await ConductEngine(session, llm=answered).handle_message(run.id, "line lead", respondent)
    run = await ConductEngine(session, llm=FakeLLM(_record(4))).handle_message(
        run.id, "4", respondent
    )
    assert run.status is RunStatus.completed

    await ConductEngine(session, llm=FakeLLM()).delete_run(run.id, respondent)

    with pytest.raises(NotFoundError):
        await ConductEngine(session, llm=FakeLLM()).load(run.id, respondent)


async def test_one_respondent_cannot_erase_another_persons_run(
    session, respondent, other_respondent, published
):
    """The same ownership gate reading and rewinding get. Erasure reachable by guessing a
    run id would be a way to delete someone else's answers, which is worse than reading
    them: it cannot be undone and leaves the author's totals quietly short."""
    engine = ConductEngine(session, llm=FakeLLM())
    run = await engine.start_run(published.id, respondent)

    with pytest.raises(ForbiddenError):
        await ConductEngine(session, llm=FakeLLM()).delete_run(run.id, other_respondent)

    assert await ConductEngine(session, llm=FakeLLM()).load(run.id, respondent) is not None


async def test_erasing_a_run_removes_it_from_the_authors_results(
    session, author, respondent, other_respondent, published
):
    """The author's totals drop, which is the point rather than a side effect: a count
    that survived the withdrawal of the answers behind it is a number with nothing
    under it."""
    from app.runs.service import ResultsService

    kept = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    await ConductEngine(session, llm=FakeLLM(_record("Line lead"), _move_on())).handle_message(
        kept.id, "line lead", respondent
    )
    withdrawn = await ConductEngine(session, llm=FakeLLM()).start_run(
        published.id, other_respondent
    )
    await ConductEngine(session, llm=FakeLLM(_record("Packer"), _move_on())).handle_message(
        withdrawn.id, "packer", other_respondent
    )
    assert len(await ResultsService(session).list_runs(published.id, author)) == 2

    await ConductEngine(session, llm=FakeLLM()).delete_run(withdrawn.id, other_respondent)

    remaining = await ResultsService(session).list_runs(published.id, author)
    assert [s.id for s in remaining] == [kept.id]


async def test_a_twice_refused_answer_asks_rather_than_failing(session, respondent, published):
    """The failure this replaces cost a respondent their answer.

    A live run refused the model's reading of "if it's a bit over we re-ice it and carry
    on, if it's properly warm i call the supervisor" twice, and the engine raised, which
    the HTTP boundary renders as 503 "the assistant is briefly unavailable, try again in
    a moment". Every provider call had returned 200; the gate had refused the model's
    content. Retrying re-runs the same turn against the same message, so the advice was
    wrong as well as the diagnosis, and the reply was lost.

    An answer the engine cannot accept is what a probe is for.
    """
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    ungrounded = _record("Nowhere I can see")  # supported by nothing they said
    llm = FakeLLM(ungrounded, ungrounded, _follow_up("Which of those is closest?", None))

    run = await ConductEngine(session, llm=llm).handle_message(
        run.id, "training new starters, thats where wed feel it", respondent
    )

    # A question, not an error, and the survey is still on the same question.
    assert run.messages[-1].content == "Which of those is closest?"
    assert run.current_question_index == 0
    assert not run.answers
    assert llm.calls == 3
    # The third call is offered the probe alone: recording is what just failed twice.
    assert list(llm.offered[2]) == ["ask_follow_up"]


async def test_the_fallback_probe_is_bounded_by_the_budget(session, respondent, published):
    """The probe budget is what stops this looping. With none left the turn fails, because
    at that point there is nothing further to try and hiding it would be worse."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    for _ in range(MAX_FOLLOW_UPS):
        run = await ConductEngine(
            session, llm=FakeLLM(_follow_up("Say more?", None))
        ).handle_message(run.id, "hm", respondent)

    ungrounded = _record("Nowhere I can see")
    llm = FakeLLM(ungrounded, ungrounded)
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=llm).handle_message(run.id, "training", respondent)

    assert llm.calls == 2  # no fallback offered: there was no probe left to offer
