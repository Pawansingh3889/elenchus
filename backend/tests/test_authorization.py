"""One author must not reach another author's surveys or responses.

Dev-auth is a deliberate trial simplification, but these boundaries are enforced in the
services rather than in the auth layer, so they hold unchanged once a real identity
provider supplies the caller.
"""

import pytest

from app.auth.dependencies import get_current_user, require_author
from app.conduct.engine import ConductEngine
from app.errors import ForbiddenError, NotFoundError, UnauthorizedError
from app.runs.service import ResultsService
from app.templates.enums import AnswerType, SurveyAudience, TemplateStatus
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
    """Not found rather than forbidden, so the API can't be used to enumerate ids.

    Aimed at operatives, which the finance manager is not: a survey whose audience the
    caller is outside of does not exist for them. An `everyone` survey is a different
    case since the job model, tested separately below, because a finance manager holds
    a job and may answer it, so it is visible to them and merely not editable.
    """
    svc = TemplateService(session)
    mine = await svc.create_draft(
        TemplateCreate(title="Mine", audience=SurveyAudience.operatives, questions=[_q("a")]),
        author,
    )

    with pytest.raises(NotFoundError):
        if action == "get":
            await svc.get_draft(mine.id, other_author)
        elif action == "update":
            await svc.update_draft(
                mine.id, update_of(mine, title="Hijacked", questions=[_q("x")]), other_author
            )
        elif action == "delete":
            await svc.delete_survey(mine.id, other_author)
        else:
            await svc.publish(mine.id, other_author)


@pytest.mark.parametrize("action", ["update", "delete", "publish"])
async def test_a_visible_survey_is_still_not_editable_by_a_stranger(
    session, author, other_author, action
):
    """The two-step refusal the job model introduced. An `everyone` survey is visible to
    every jobbed person because they may answer it, so hiding it from the finance
    manager would be lying; what they get on a mutation is a plain forbidden, because
    visibility has never implied the write path."""
    svc = TemplateService(session)
    mine = await svc.create_draft(TemplateCreate(title="Mine", questions=[_q("a")]), author)
    assert (await svc.get_draft(mine.id, other_author)).id == mine.id

    with pytest.raises(ForbiddenError):
        if action == "update":
            await svc.update_draft(
                mine.id, update_of(mine, title="Hijacked", questions=[_q("x")]), other_author
            )
        elif action == "delete":
            await svc.delete_survey(mine.id, other_author)
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


async def test_only_authors_can_build(author, respondent):
    """The mirror gate: building surveys stays closed to respondents."""
    assert await require_author(user=author) is author
    with pytest.raises(ForbiddenError):
        await require_author(user=respondent)


async def test_the_published_list_is_what_the_reader_may_actually_start(
    session, author, respondent, other_author
):
    """The list is an answer to "what may *you* start", not a catalogue.

    An `everyone` survey reaches everyone with a job now, office managers included, so
    the finance manager is shown it: under the membership model an office account in no
    group was in no audience at all, and that exclusion was always a bit false. The
    boundary still exists where it was aimed: a survey for operatives is not offered to
    the finance manager.
    """
    svc = TemplateService(session)
    mine = await svc.create_draft(TemplateCreate(title="Open", questions=[_q("a")]), author)
    await svc.publish(mine.id, author)
    floor = await svc.create_draft(
        TemplateCreate(title="Floor only", audience=SurveyAudience.operatives, questions=[_q("b")]),
        author,
    )
    await svc.publish(floor.id, author)

    listed = await svc.list_published(respondent)
    assert sorted(t.title for t, _, _, _ in listed) == ["Floor only", "Open"]
    assert all(t.status is TemplateStatus.published for t, _, _, _ in listed)

    assert [t.title for t, _, _, _ in await svc.list_published(other_author)] == ["Open"]


# --- the dev-auth user list, which is available for public survey access ----------


def test_the_user_list_requires_a_known_caller():
    """Under the shim a user's id IS their credential, so an open list of every id was an
    open list of every credential. Requiring a caller means the list can no longer be how
    someone gets their first id."""
    from app.users.router import router

    route = next(r for r in router.routes if getattr(r, "path", "") == "/api/v1/users")
    assert get_current_user in {d.call for d in route.dependant.dependencies}


async def test_a_caller_with_no_credential_is_nobody(session):
    """The one that would have caught it, so it is worth saying what "it" was.

    Between 24 Aug and 27 Aug 2026 this branch substituted a hardcoded seeded id when a
    request carried neither cookie nor header. That id was the account whose address is
    also ADMIN_EMAILS, so an anonymous request to the deployed service was an
    administrator: /api/v1/me answered "is_admin": true to a stranger and the admin
    surface served without a credential. Nothing failed, because no test asked what an
    anonymous caller gets.

    A missing credential is missing required data, and this project does not shrug at
    that. The assertion is the type: a 401, not a user.
    """
    with pytest.raises(UnauthorizedError):
        await get_current_user(x_user_id=None, elenchus_session=None, session=session)


async def test_an_unknown_id_is_also_nobody(session):
    """The neighbouring branch, pinned so a future fix cannot 'helpfully' fall back to a
    default user when the id does not resolve."""
    from uuid import uuid4

    with pytest.raises(UnauthorizedError):
        await get_current_user(x_user_id=uuid4(), elenchus_session=None, session=session)
