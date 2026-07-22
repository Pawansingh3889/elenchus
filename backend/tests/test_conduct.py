"""Conduct engine tests. The LLM is faked at the client boundary, so every assertion
here is about the engine's own decisions: what it offers, what it accepts, what it
refuses, and where run state lives.
"""

import pytest

from app.conduct.engine import MAX_FOLLOW_UPS, ConductEngine
from app.errors import ConflictError
from app.llm.client import LLMError, ToolTurn
from app.runs.enums import AnswerKind, RunStatus
from app.templates.enums import AnswerType
from app.templates.schemas import QuestionInput, TemplateUpdate
from app.templates.service import TemplateService
from tests.fakes import FakeLLM
from tests.fakes import follow_up as _follow_up
from tests.fakes import move_on as _move_on
from tests.fakes import record as _record


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
