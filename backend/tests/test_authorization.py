"""One author must not reach another author's surveys or responses.

Dev-auth is a deliberate trial simplification, but these boundaries are enforced in the
services rather than in the auth layer, so they hold unchanged once a real identity
provider supplies the caller.
"""

import pytest

from app.auth.dependencies import require_author, require_respondent
from app.conduct.engine import ConductEngine
from app.errors import ForbiddenError, NotFoundError
from app.runs.service import ResultsService
from app.templates.enums import AnswerType, TemplateStatus
from app.templates.schemas import QuestionInput, TemplateCreate, TemplateUpdate
from app.templates.service import TemplateService
from tests.fakes import FakeLLM, move_on, record


def _q(text: str) -> QuestionInput:
    return QuestionInput(text=text, answer_type=AnswerType.short_text)


async def test_an_author_only_lists_their_own_templates(session, author, other_author):
    svc = TemplateService(session)
    await svc.create_draft(TemplateCreate(title="Mine", questions=[_q("a")]), author)
    await svc.create_draft(TemplateCreate(title="Theirs", questions=[_q("b")]), other_author)

    mine = await svc.list_drafts(None, author)
    theirs = await svc.list_drafts(None, other_author)

    assert [t.title for t, _ in mine] == ["Mine"]
    assert [t.title for t, _ in theirs] == ["Theirs"]


@pytest.mark.parametrize("action", ["get", "update", "delete", "publish"])
async def test_another_authors_template_reads_as_absent(session, author, other_author, action):
    """Not found rather than forbidden, so the API can't be used to enumerate ids."""
    svc = TemplateService(session)
    mine = await svc.create_draft(TemplateCreate(title="Mine", questions=[_q("a")]), author)

    with pytest.raises(NotFoundError):
        if action == "get":
            await svc.get_draft(mine.id, other_author)
        elif action == "update":
            await svc.update_draft(
                mine.id, TemplateUpdate(title="Hijacked", questions=[_q("x")]), other_author
            )
        elif action == "delete":
            await svc.delete_draft(mine.id, other_author)
        else:
            await svc.publish(mine.id, other_author)


async def test_an_author_cannot_read_another_authors_responses(
    session, author, other_author, respondent, published
):
    """Responses carry respondent names and verbatim transcripts — the sensitive read."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, respondent)
    llm = FakeLLM(record("Line lead"), move_on())
    await ConductEngine(session, llm=llm).handle_message(run.id, "line lead", respondent)

    results = ResultsService(session)
    assert len(await results.list_runs(published.id, author)) == 1

    with pytest.raises(NotFoundError):
        await results.list_runs(published.id, other_author)
    with pytest.raises(NotFoundError):
        await results.get_run(published.id, run.id, other_author)


async def test_only_respondents_can_take_surveys(author, respondent):
    """Taking a survey is respondent-only; an author is refused before a run is created."""
    assert await require_respondent(user=respondent) is respondent
    with pytest.raises(ForbiddenError):
        await require_respondent(user=author)


async def test_only_authors_can_build(author, respondent):
    """The mirror gate: building surveys stays closed to respondents."""
    assert await require_author(user=author) is author
    with pytest.raises(ForbiddenError):
        await require_author(user=respondent)


async def test_published_surveys_stay_visible_to_everyone(session, author, other_author):
    """Published surveys aren't scoped per author; only starting a run is role-gated
    (respondent-only), and authoring/results stay author-scoped."""
    svc = TemplateService(session)
    mine = await svc.create_draft(TemplateCreate(title="Open", questions=[_q("a")]), author)
    await svc.publish(mine.id, author)

    listed = await svc.list_published()

    assert [t.title for t, _, _ in listed] == ["Open"]
    assert all(t.status is TemplateStatus.published for t, _, _ in listed)
