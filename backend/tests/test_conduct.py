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

    llm = FakeLLM(_record("done"), _follow_up("one more?"), _follow_up("please?"))
    with pytest.raises(LLMError):
        await ConductEngine(session, llm=llm).handle_message(run.id, "no", respondent)
    assert llm.calls == 3  # record, then the rejected probe and its one retry


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
