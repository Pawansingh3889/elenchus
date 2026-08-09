"""Closing a survey: what it stops, and what it deliberately does not.

Closed means the study is over. The engine refuses to start a new conversation against a
closed survey, and a conversation already under way finishes on its own terms. Stopping
mid-question would throw away answers a respondent has already given, and for a chat that
is a worse bargain than a final count that settles a few minutes late.
"""

import pytest

from app.conduct.engine import ConductEngine
from app.errors import ConflictError, NotFoundError
from app.runs.enums import RunStatus
from app.templates.enums import TemplateStatus
from app.templates.service import TemplateService
from tests.fakes import FakeLLM
from tests.fakes import move_on as _move_on
from tests.fakes import record as _record


async def test_closing_sets_the_status_and_the_date(session, author, published):
    template = await TemplateService(session).close(published.id, author)
    assert template.status is TemplateStatus.closed
    assert template.closed_at is not None


async def test_a_closed_survey_refuses_a_new_run(session, author, respondent, published):
    await TemplateService(session).close(published.id, author)
    with pytest.raises(ConflictError) as caught:
        await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    # The respondent followed a link that used to work, so the message has to say the
    # survey is over rather than blame the template for having no published version.
    assert "closed" in caught.value.message.lower()


async def test_a_conversation_already_under_way_still_finishes(
    session, author, respondent, published
):
    """The case worth having. Someone is mid-survey when the author closes it."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    # q0 permits probing, so the engine loops once more for the probe decision.
    llm = FakeLLM(_record("Warehouse supervisor"), _move_on("Thanks. How was onboarding?"))
    run = await ConductEngine(session, llm=llm).handle_message(
        run.id, "warehouse supervisor", respondent
    )
    assert run.status is RunStatus.in_progress

    await TemplateService(session).close(published.id, author)

    run = await ConductEngine(session, llm=FakeLLM(_record(4))).handle_message(
        run.id, "4", respondent
    )
    assert run.status is RunStatus.completed
    assert len(run.answers) == 2


async def test_only_a_published_survey_can_be_closed(session, author):
    """A draft never opened, and closing twice would move the date an author quotes."""
    svc = TemplateService(session)
    with pytest.raises(ConflictError):
        await svc.close((await _a_draft(svc, author)).id, author)


async def test_closing_someone_elses_survey_reads_as_absent(session, other_author, published):
    """Same rule as the rest of the template API: not yours reads as missing, so the
    endpoint cannot be used to find out which ids exist."""
    with pytest.raises(NotFoundError):
        await TemplateService(session).close(published.id, other_author)


async def _a_draft(svc: TemplateService, author):
    from app.templates.enums import AnswerType
    from app.templates.schemas import QuestionInput, TemplateCreate

    return await svc.create_draft(
        TemplateCreate(
            title="Not yet open",
            questions=[QuestionInput(text="Anything?", answer_type=AnswerType.short_text)],
        ),
        author,
    )
