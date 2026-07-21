"""Reading results back: what an author gets, and what they are refused.

Results cross respondents by design, so the boundary that matters here is the template
a run belongs to, not the person who answered it.
"""

from uuid import uuid4

import pytest

from app.conduct.engine import ConductEngine
from app.errors import NotFoundError
from app.runs.enums import RunStatus
from app.runs.service import ResultsService
from app.templates.enums import AnswerType
from app.templates.schemas import QuestionInput, TemplateCreate, TemplateUpdate
from app.templates.service import TemplateService
from tests.fakes import FakeLLM, follow_up, move_on, record


async def _answer_first(session, run, respondent):
    llm = FakeLLM(record("Line lead"), move_on())
    return await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)


async def test_lists_who_answered_and_how_far_they_got(session, respondent, published):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    await _answer_first(session, run, respondent)

    summaries = await ResultsService(session).list_runs(published.id)

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.id == run.id
    assert summary.respondent_name == "Test Respondent"
    assert summary.status is RunStatus.in_progress
    assert (summary.answered, summary.total) == (1, 2)
    assert summary.version == 1
    assert summary.completed_at is None


async def test_a_run_is_reported_against_the_version_it_answered(
    session, author, respondent, published
):
    """The author rewrites the survey mid-run; the response must not be re-scored."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    await _answer_first(session, run, respondent)

    svc = TemplateService(session)
    await svc.update_draft(
        published.id,
        TemplateUpdate(
            title="Rewritten",
            questions=[QuestionInput(text="One question now", answer_type=AnswerType.long_text)],
        ),
        author,
    )
    assert (await svc.publish(published.id, author)).version == 2

    summary = (await ResultsService(session).list_runs(published.id))[0]
    assert summary.version == 1
    assert summary.total == 2  # v1's question count, not v2's


async def test_detail_returns_the_answers_and_the_transcript(session, respondent, published):
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    await _answer_first(session, run, respondent)

    detail = await ResultsService(session).get_run(published.id, run.id)

    assert detail.respondent_name == "Test Respondent"
    assert [a.question_text for a in detail.answers] == ["What's your role?"]
    assert detail.answers[0].value == {"text": "Line lead"}
    assert [m.role.value for m in detail.messages] == ["assistant", "user", "assistant"]


async def test_a_follow_up_is_ordered_under_the_question_it_probed(session, respondent, published):
    """Results attach a follow-up to its parent, so ordering and the shared id both matter."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    probe = FakeLLM(record("Line lead"), follow_up("What does that involve day to day?"))
    run = await ConductEngine(session, llm=probe).handle_message(run.id, "line lead", respondent)
    reply = FakeLLM(record("Running the handover"), move_on())
    await ConductEngine(session, llm=reply).handle_message(run.id, "the handover", respondent)

    answers = (await ResultsService(session).get_run(published.id, run.id)).answers

    assert [a.kind.value for a in answers] == ["scripted", "follow_up"]
    assert answers[0].question_id == answers[1].question_id  # the follow-up's parent
    assert answers[0].answered_at < answers[1].answered_at
    assert answers[1].question_text == "What does that involve day to day?"


async def test_a_run_from_another_template_is_not_found(session, author, respondent, published):
    other = await TemplateService(session).create_draft(
        TemplateCreate(
            title="A different survey",
            questions=[QuestionInput(text="Anything?", answer_type=AnswerType.short_text)],
        ),
        author,
    )
    await TemplateService(session).publish(other.id, author)
    stray = await ConductEngine(session, llm=FakeLLM()).start_run(other.id, respondent)

    with pytest.raises(NotFoundError):
        await ResultsService(session).get_run(published.id, stray.id)


async def test_missing_template_is_not_found(session, published):
    with pytest.raises(NotFoundError):
        await ResultsService(session).list_runs(uuid4())
