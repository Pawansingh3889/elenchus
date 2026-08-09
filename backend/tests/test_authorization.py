"""One author must not reach another author's surveys or responses.

Dev-auth is a deliberate trial simplification, but these boundaries are enforced in the
services rather than in the auth layer, so they hold unchanged once a real identity
provider supplies the caller.
"""

import pytest

from app.auth.dependencies import get_current_user, require_author, require_respondent
from app.conduct.engine import ConductEngine
from app.errors import ForbiddenError, NotFoundError
from app.runs.service import ResultsService
from app.templates.enums import AnswerType, TemplateStatus
from app.templates.schemas import QuestionInput, TemplateCreate
from app.templates.service import TemplateService
from tests.builders import update_of
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
                mine.id, update_of(mine, title="Hijacked", questions=[_q("x")]), other_author
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


async def test_the_published_list_is_what_the_reader_may_actually_start(
    session, author, respondent, other_author
):
    """This used to assert published surveys were visible to everyone, which was true
    when every survey was aimed at the whole respondent pool and is the assumption
    audiences exist to replace. A survey aimed at respondents still reaches every
    respondent, so the old behaviour is intact where it was ever meant to apply. What has
    changed is that the list is now an answer to "what may *you* start", not a catalogue:
    another author, who cannot answer it, is not shown it either."""
    svc = TemplateService(session)
    mine = await svc.create_draft(TemplateCreate(title="Open", questions=[_q("a")]), author)
    await svc.publish(mine.id, author)

    listed = await svc.list_published(respondent)
    assert [t.title for t, _, _ in listed] == ["Open"]
    assert all(t.status is TemplateStatus.published for t, _, _ in listed)

    assert await svc.list_published(other_author) == []


# --- the dev-auth user list, which must not outlive the dev auth -----------------


def test_the_user_list_requires_a_known_caller():
    """Under the shim a user's id IS their credential, so an open list of every id was an
    open list of every credential. Requiring a caller means the list can no longer be how
    someone gets their first id."""
    from app.users.router import router

    route = next(r for r in router.routes if getattr(r, "path", "") == "/api/v1/users")
    assert get_current_user in {d.call for d in route.dependant.dependencies}


def test_the_user_list_is_not_mounted_outside_development(monkeypatch):
    """Absent beats guarded. An endpoint that was never registered cannot be reached by a
    bug in whatever guards it, and a deployment seeds nobody, so the picker this exists
    for would have nothing to show.

    Also the first thing in the codebase to branch on APP_ENV, which the deployment file
    has been carrying a note about changing no behaviour.
    """
    import importlib

    import app.main
    from app.config import get_settings

    def mounted_paths() -> set[str]:
        # The generated spec rather than app.routes: included routers nest rather than
        # flatten, so walking routes misses everything mounted through include_router.
        get_settings.cache_clear()
        return set(importlib.reload(app.main).app.openapi()["paths"])

    monkeypatch.setenv("APP_ENV", "prod")
    assert "/api/v1/users" not in mounted_paths()

    monkeypatch.setenv("APP_ENV", "dev")
    assert "/api/v1/users" in mounted_paths()  # restores the module for later tests
