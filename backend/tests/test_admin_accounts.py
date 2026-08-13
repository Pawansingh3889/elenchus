"""Creating accounts, and deciding what somebody is.

This is the first path in the app that writes `users.role`, so it is the first thing that
answers "who can be an author" with something other than "whoever can reach the database".
That makes the refusals the interesting half: each one below describes a row the access
rules would go on to read as something nobody meant.

Service level rather than over HTTP, like the rest of the suite. The boundary being
tested is in `UserService` and on the schemas, so it holds whatever eventually supplies
the caller.
"""

from uuid import uuid4

import pytest
import pytest_asyncio
from pydantic import ValidationError as PydanticValidationError

from app.auth.dependencies import require_admin
from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.templates.enums import SurveyAudience, TemplateStatus
from app.templates.models import SurveyTemplate
from app.users.models import CreatorDepartment, RespondentGroup, User, UserRole
from app.users.repository import UserRepository
from app.users.schemas import AccountCreate, AccountUpdate, MeRead, PersonRead
from app.users.service import UserService


def _floor(**kw) -> AccountCreate:
    """A valid floor account: answers surveys, in a group, no department."""
    return AccountCreate(
        **{
            "email": "rosa@plant.dev",
            "display_name": "Rosa",
            "role": UserRole.respondent,
            "groups": [RespondentGroup.operatives],
            **kw,
        }
    )


def _creator(**kw) -> AccountCreate:
    """A valid author: has a department, and so has colleagues."""
    return AccountCreate(
        **{
            "email": "ava@plant.dev",
            "display_name": "Ava",
            "role": UserRole.author,
            "department": CreatorDepartment.hr,
            **kw,
        }
    )


def _update_of(create: AccountCreate, **kw) -> AccountUpdate:
    """The same account as an update, which carries every field but the email."""
    fields = create.model_dump(exclude={"email"})
    return AccountUpdate(**{**fields, **kw})


@pytest_asyncio.fixture
async def admin(session):
    """An administrator by department. IT is what grants it, per app/access.

    Flushed, like the other user fixtures: `id` defaults at flush, so an unflushed User
    has none, and `created_by=admin.id` would quietly stamp null.
    """
    user = User(
        email="it@plant.dev",
        display_name="IT",
        role=UserRole.author,
        department=CreatorDepartment.it,
    )
    session.add(user)
    await session.flush()
    return user


# --- who may use this at all -------------------------------------------------------


async def test_an_ordinary_author_is_not_an_administrator(author):
    """The gate is `is_admin`, which never consults `role`.

    An author is the *most* privileged ordinary account and still may not create people.
    Being able to write surveys has never implied being able to decide who answers them.
    """
    with pytest.raises(ForbiddenError):
        await require_admin(author)


async def test_a_respondent_in_it_still_administers(session):
    """`require_admin` is deliberately not layered on `require_author`.

    An administrator whose own account is a respondent must still reach the screen that
    would fix that, or the mistake is unrecoverable from inside the app.
    """
    user = User(
        email="it2@plant.dev",
        display_name="IT Two",
        role=UserRole.respondent,
        department=CreatorDepartment.it,
    )
    assert await require_admin(user) is user


# --- creating ----------------------------------------------------------------------


async def test_creating_a_floor_account_records_who_created_it(session, admin):
    created = await UserService(session).create_account(_floor(), admin)

    assert created.role is UserRole.respondent
    assert created.groups == frozenset({RespondentGroup.operatives})
    assert created.created_by == admin.id


async def test_an_account_the_seed_made_has_no_creator(session, author):
    """Null means "nobody in this app created this", not a value somebody forgot.

    Every account predating the admin screen is in this state, and so is every account a
    real Microsoft sign-in will provision, because those arrive from outside the app.
    """
    assert author.created_by is None


async def test_the_groups_asked_for_are_the_groups_they_get(session, admin):
    created = await UserService(session).create_account(
        _floor(groups=[RespondentGroup.line_leaders, RespondentGroup.qa]), admin
    )
    assert created.groups == frozenset({RespondentGroup.line_leaders, RespondentGroup.qa})


async def test_an_author_may_also_be_on_the_floor(session, admin):
    """The case the whole membership model exists for.

    A supervisor signs in with Teams, so holds an author account, and is still somebody a
    survey aimed at supervisors was written for.
    """
    created = await UserService(session).create_account(
        _creator(groups=[RespondentGroup.supervisors]), admin
    )
    assert created.role is UserRole.author
    assert RespondentGroup.supervisors in created.groups


# --- the refusals ------------------------------------------------------------------


def test_an_author_without_a_department_is_refused():
    """A creator without one is a misconfiguration rather than a state (CLAUDE.md).

    It decides who their colleagues are, and for `it` whether they administer the system.
    """
    with pytest.raises(PydanticValidationError, match="department"):
        _creator(department=None)


def test_a_respondent_with_a_department_is_refused():
    """The load-bearing refusal, and the reason is a leak rather than tidiness.

    `_colleague` in app/access/rules.py makes anyone sharing a department a colleague, and
    `may_read_rows` hands a colleague every individual answer. A respondent given `hr`
    would quietly gain the raw answers to every survey HR has ever run, which is the exact
    opposite of what the pseudonymity elsewhere in this system promises them.
    """
    with pytest.raises(PydanticValidationError, match="Only an author has a department"):
        _floor(department=CreatorDepartment.hr)


def test_a_respondent_in_no_group_is_refused():
    """Somebody in no group can be asked nothing at all, not even a survey for everyone.

    `may_answer` refuses an empty `user.groups` on the `everyone` branch, so an account
    like this is a person nobody can survey. That is the blocker CLAUDE.md names, and it
    would otherwise be created silently by leaving one field alone.
    """
    with pytest.raises(PydanticValidationError, match="at least one group"):
        _floor(groups=[])


def test_the_same_group_twice_is_refused():
    """The membership key is (user_id, group), so this is otherwise an IntegrityError:
    the same refusal, several layers too late to name the field that caused it."""
    with pytest.raises(PydanticValidationError, match="twice"):
        _floor(groups=[RespondentGroup.qa, RespondentGroup.qa])


def test_an_address_with_no_at_sign_is_refused():
    with pytest.raises(PydanticValidationError, match="email address"):
        _floor(email="rosa-at-plant")


def test_a_name_of_only_spaces_is_refused():
    """`min_length` passes on "   ", which then renders as an empty cell everywhere."""
    with pytest.raises(PydanticValidationError, match="name is required"):
        _floor(display_name="   ")


# --- identifiers -------------------------------------------------------------------


async def test_the_address_is_stored_folded(session, admin):
    """`is_admin` folds both sides when matching the allowlist; the unique index does not.

    Without folding on the way in, `Rosa@plant.dev` and `rosa@plant.dev` are two rows, two
    identities, and one allowlist entry that would let both administer.
    """
    created = await UserService(session).create_account(_floor(email="Rosa@Plant.dev"), admin)
    assert created.email == "rosa@plant.dev"


async def test_a_second_account_on_one_address_is_a_conflict(session, admin):
    svc = UserService(session)
    await svc.create_account(_floor(), admin)

    with pytest.raises(ConflictError, match="already has an account"):
        await svc.create_account(_floor(display_name="Someone else"), admin)


async def test_folding_is_what_catches_the_duplicate(session, admin):
    """The case the unique index alone would miss, which is why folding is on the way in."""
    svc = UserService(session)
    await svc.create_account(_floor(email="rosa@plant.dev"), admin)

    with pytest.raises(ConflictError):
        await svc.create_account(_floor(email="ROSA@plant.dev"), admin)


async def test_two_accounts_may_not_share_a_microsoft_id(session, admin):
    """It is an identity. Two accounts carrying one would be two people sharing it."""
    svc = UserService(session)
    await svc.create_account(_creator(microsoft_id="entra-ava"), admin)

    with pytest.raises(ConflictError, match="Microsoft id"):
        await svc.create_account(_creator(email="other@plant.dev", microsoft_id="entra-ava"), admin)


async def test_a_blank_microsoft_id_is_absent_rather_than_empty(session, admin):
    """A form posts "" for a field somebody tabbed through, and "" is not an account.

    Stored as written it would occupy the unique index, and the *second* account created
    without one would come back as a conflict naming a field nobody filled in.
    """
    svc = UserService(session)
    first = await svc.create_account(_floor(microsoft_id="  "), admin)
    second = await svc.create_account(_floor(email="ravi@plant.dev", microsoft_id=""), admin)

    assert first.microsoft_id is None
    assert second.microsoft_id is None


# --- replacing ---------------------------------------------------------------------


async def test_an_update_removes_the_groups_it_leaves_out(session, admin):
    """The reason the update is a replacement and not a patch.

    Somebody moves off a line. A body that only ever added would make that unexpressible
    through this screen, and the account would keep a membership that decides which
    surveys reach them.
    """
    svc = UserService(session)
    created = await svc.create_account(
        _floor(groups=[RespondentGroup.line_leaders, RespondentGroup.qa]), admin
    )

    changed = await svc.replace_account(
        created.id, _update_of(_floor(groups=[RespondentGroup.qa])), admin
    )

    assert changed.groups == frozenset({RespondentGroup.qa})


async def test_granting_authorship_is_a_change_of_role_and_department(session, admin):
    """The answer to "who decides who can be an author": an administrator, here."""
    svc = UserService(session)
    created = await svc.create_account(_floor(), admin)

    changed = await svc.replace_account(
        created.id,
        _update_of(_floor(), role=UserRole.author, department=CreatorDepartment.technical),
        admin,
    )

    assert changed.role is UserRole.author
    assert changed.department is CreatorDepartment.technical


async def test_an_absent_account_is_not_found(session, admin):
    with pytest.raises(NotFoundError):
        await UserService(session).replace_account(uuid4(), _update_of(_floor()), admin)


async def test_an_administrator_cannot_edit_away_their_own_administration(session, admin):
    """Unrecoverable from inside the app, which is what makes it worth a special case.

    The last administrator moves themselves out of IT, and from then on nobody can create
    an account or grant anybody else the department that would let them. The fix is a
    database edit, which is the thing this screen exists to stop being necessary.
    """
    with pytest.raises(ConflictError, match="your own administrator access"):
        await UserService(session).replace_account(
            admin.id,
            AccountUpdate(
                display_name="IT",
                role=UserRole.author,
                department=CreatorDepartment.management,
            ),
            admin,
        )


async def test_one_administrator_may_still_demote_another(session, admin):
    """Only their own account is protected. Removing somebody else's is a real thing to do."""
    svc = UserService(session)
    other = await svc.create_account(_creator(department=CreatorDepartment.it), admin)

    changed = await svc.replace_account(
        other.id, _update_of(_creator(department=CreatorDepartment.finance)), admin
    )

    assert changed.department is CreatorDepartment.finance


# --- what the screens read ---------------------------------------------------------


def test_me_reports_administration_the_browser_could_not_work_out(admin):
    """Half of `is_admin` is an allowlist in server settings, deliberately not shipped.

    A client deciding this locally would decide it wrongly for every administrator who is
    not in the IT department.
    """
    me = MeRead(
        id=admin.id,
        display_name=admin.display_name,
        role=admin.role,
        department=admin.department,
        is_admin=True,
    )
    assert me.is_admin


def test_the_directory_marks_an_author_who_could_not_sign_in(session):
    """`role` is stored as sent, so this pair can drift, and the drift is invisible.

    An author with no Entra id may build surveys today and will stop being able to the day
    `role` is derived from that id instead. The directory carries the flag so the screen
    can say so while somebody is still looking at the account.
    """
    author_without = User(
        id=uuid4(),
        email="a@plant.dev",
        display_name="A",
        role=UserRole.author,
        department=CreatorDepartment.hr,
    )
    author_with = User(
        id=uuid4(),
        email="b@plant.dev",
        display_name="B",
        role=UserRole.author,
        department=CreatorDepartment.hr,
        microsoft_id="entra-b",
    )

    assert PersonRead.of(author_without).has_microsoft_id is False
    assert PersonRead.of(author_with).has_microsoft_id is True


# --- the audit log -----------------------------------------------------------------


async def test_creating_an_account_writes_its_first_history_row(session, admin):
    svc = UserService(session)
    created = await svc.create_account(_floor(), admin)

    (entry,) = await svc.history(created.id)

    assert entry.kind == "created"
    assert entry.before is None
    assert entry.after.groups == [RespondentGroup.operatives]
    assert entry.changed_by == admin.id
    assert entry.changed_by_name == admin.display_name


async def test_an_edit_records_what_it_was_and_what_it_became(session, admin):
    """The row is the answer to "why did reach move on Tuesday"."""
    svc = UserService(session)
    created = await svc.create_account(_floor(groups=[RespondentGroup.qa]), admin)

    await svc.replace_account(
        created.id, _update_of(_floor(groups=[RespondentGroup.line_leaders])), admin
    )

    newest, oldest = await svc.history(created.id)
    assert oldest.kind == "created"
    assert newest.kind == "updated"
    assert newest.before is not None
    assert newest.before.groups == [RespondentGroup.qa]
    assert newest.after.groups == [RespondentGroup.line_leaders]


async def test_a_save_that_changed_nothing_writes_nothing(session, admin):
    """PUT is a full replacement, so an untouched form is a legitimate no-op.

    Logging it would bury the edits that moved a reach number under rows that moved
    nothing, and a log nobody can read for the signal stops being consulted at all.
    """
    svc = UserService(session)
    created = await svc.create_account(_floor(), admin)

    await svc.replace_account(created.id, _update_of(_floor()), admin)

    entries = await svc.history(created.id)
    assert [e.kind for e in entries] == ["created"]


async def test_history_of_an_absent_account_is_not_found(session, admin):
    with pytest.raises(NotFoundError):
        await UserService(session).history(uuid4())


# --- the what-if preview -----------------------------------------------------------


def _published_survey(author_id, audience, title="Open survey", target=None) -> SurveyTemplate:
    return SurveyTemplate(
        title=title,
        audience=audience,
        audience_user_id=target,
        created_by=author_id,
        status=TemplateStatus.published,
    )


async def test_preview_names_the_open_survey_a_person_would_leave(session, admin, author):
    """The guardrail itself: the moment before reach moves is when the mover sees it.

    Rosa is the only QA member and an open survey is aimed at QA, so moving her off the
    line takes that survey's reach from one to zero. The preview must say so, by title,
    with both numbers, before anything is saved.
    """
    svc = UserService(session)
    rosa = await svc.create_account(_floor(groups=[RespondentGroup.qa]), admin)
    session.add(_published_survey(author.id, SurveyAudience.qa, title="QA weekly"))
    await session.flush()

    impact = await svc.preview_change(
        rosa.id, _update_of(_floor(groups=[RespondentGroup.operatives]))
    )

    assert impact.groups_added == [RespondentGroup.operatives]
    assert impact.groups_removed == [RespondentGroup.qa]
    (survey,) = impact.surveys
    assert survey.title == "QA weekly"
    assert survey.now_in is False
    assert (survey.reach_before, survey.reach_after) == (1, 0)


async def test_preview_names_the_open_survey_a_person_would_join(session, admin, author):
    svc = UserService(session)
    rosa = await svc.create_account(_floor(), admin)
    session.add(_published_survey(author.id, SurveyAudience.qa, title="QA weekly"))
    await session.flush()

    impact = await svc.preview_change(
        rosa.id, _update_of(_floor(groups=[RespondentGroup.operatives, RespondentGroup.qa]))
    )

    (survey,) = impact.surveys
    assert survey.now_in is True
    assert (survey.reach_before, survey.reach_after) == (0, 1)


async def test_preview_is_silent_about_surveys_the_edit_does_not_touch(session, admin, author):
    """Membership is unchanged for operatives, so the operatives survey must not appear:
    a preview that lists everything teaches admins to read none of it."""
    svc = UserService(session)
    rosa = await svc.create_account(_floor(), admin)
    session.add(_published_survey(author.id, SurveyAudience.operatives, title="Ops daily"))
    await session.flush()

    impact = await svc.preview_change(rosa.id, _update_of(_floor(display_name="Renamed")))

    assert impact.surveys == []


async def test_preview_skips_drafts_and_closed_surveys(session, admin, author):
    """Only open surveys are guarded: a draft reaches nobody yet, and a closed survey
    takes no new answers, so neither has a denominator this edit can move.

    Rosa flips out of the QA audience here, and the preview must still be empty,
    because the only QA surveys that exist are a draft and a closed one.
    """
    svc = UserService(session)
    rosa = await svc.create_account(
        _floor(groups=[RespondentGroup.qa, RespondentGroup.operatives]), admin
    )
    draft = _published_survey(author.id, SurveyAudience.qa, title="Draft")
    draft.status = TemplateStatus.draft
    closed = _published_survey(author.id, SurveyAudience.qa, title="Closed")
    closed.status = TemplateStatus.closed
    session.add(draft)
    session.add(closed)
    await session.flush()

    impact = await svc.preview_change(
        rosa.id, _update_of(_floor(groups=[RespondentGroup.operatives]))
    )

    assert impact.groups_removed == [RespondentGroup.qa]
    assert impact.surveys == []


async def test_an_author_losing_their_last_group_leaves_every_everyone_survey(
    session, admin, author
):
    """The everyone audience is anyone in any group, so an author's last group is
    load-bearing: without it they are an account a survey cannot reach, and the preview
    must say which open surveys stop reaching them."""
    svc = UserService(session)
    ava = await svc.create_account(
        _creator(groups=[RespondentGroup.supervisors]),
        admin,
    )
    session.add(_published_survey(author.id, SurveyAudience.everyone, title="All hands"))
    await session.flush()

    impact = await svc.preview_change(ava.id, _update_of(_creator(groups=[])))

    (survey,) = impact.surveys
    assert survey.title == "All hands"
    assert survey.now_in is False


async def test_preview_never_reports_a_survey_aimed_at_one_person(session, admin, author):
    """The target is an id: no change of role or groups makes this user someone else,
    so a person-aimed survey cannot flip and must never show up as if it could."""
    svc = UserService(session)
    rosa = await svc.create_account(_floor(groups=[RespondentGroup.qa]), admin)
    session.add(
        _published_survey(author.id, SurveyAudience.person, title="Just Rosa", target=rosa.id)
    )
    await session.flush()

    impact = await svc.preview_change(rosa.id, _update_of(_floor(groups=[RespondentGroup.qa])))

    assert impact.surveys == []


async def test_preview_writes_nothing(session, admin, author):
    """Read-only by construction, asserted anyway: a what-if that saved would be the
    exact bug its name promises it is not."""
    svc = UserService(session)
    rosa = await svc.create_account(_floor(groups=[RespondentGroup.qa]), admin)

    await svc.preview_change(rosa.id, _update_of(_floor(groups=[RespondentGroup.operatives])))

    fresh = await UserRepository(session).get(rosa.id)
    assert fresh is not None
    assert fresh.groups == frozenset({RespondentGroup.qa})
    entries = await svc.history(rosa.id)
    assert [e.kind for e in entries] == ["created"]


async def test_preview_of_an_absent_account_is_not_found(session, admin):
    with pytest.raises(NotFoundError):
        await UserService(session).preview_change(uuid4(), _update_of(_floor()))
