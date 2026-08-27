"""Creating accounts, and deciding what somebody is.

This is the path that writes the job, and the job is what everything else derives from:
whether somebody may author (band), whether they administer (function), and which
audiences they are in. That makes the refusals the interesting half: each one below
describes a row the access rules would go on to read as something nobody meant.

Service level rather than over HTTP, like the rest of the suite. The boundary being
tested is in `UserService` and on the schemas, so it holds whatever eventually supplies
the caller.
"""

from uuid import uuid4

import pytest
import pytest_asyncio
from pydantic import ValidationError as PydanticValidationError

from app.access import in_audience, may_author
from app.auth.dependencies import require_admin
from app.config import get_settings
from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.templates.enums import SurveyAudience, TemplateStatus
from app.templates.models import SurveyTemplate
from app.users.models import Band, Function, Hat, User
from app.users.repository import UserRepository
from app.users.schemas import AccountCreate, AccountUpdate, MeRead
from app.users.service import UserService


def _floor(**kw) -> AccountCreate:
    """A valid floor account: a production operative."""
    return AccountCreate(
        **{
            "email": "rosa@plant.dev",
            "display_name": "Rosa",
            "function": Function.production,
            "band": Band.operative,
            **kw,
        }
    )


def _creator(**kw) -> AccountCreate:
    """A valid authoring account: an office manager, with colleagues in her function."""
    return AccountCreate(
        **{
            "email": "ava@plant.dev",
            "display_name": "Ava",
            "function": Function.hr,
            "band": Band.manager,
            **kw,
        }
    )


def _update_of(create: AccountCreate, **kw) -> AccountUpdate:
    """The same account as an update, which carries every field but the email."""
    fields = create.model_dump(exclude={"email"})
    return AccountUpdate(**{**fields, **kw})


@pytest_asyncio.fixture
async def admin(session):
    """An administrator by function. IT is what grants it, per app/access.

    Flushed, like the other user fixtures: `id` defaults at flush, so an unflushed User
    has none, and `created_by=admin.id` would quietly stamp null.
    """
    user = User(
        email="it@plant.dev",
        display_name="IT",
        function=Function.it,
        band=Band.manager,
    )
    session.add(user)
    await session.flush()
    return user


# --- who may use this at all -------------------------------------------------------


async def test_an_ordinary_author_is_not_an_administrator(author):
    """The gate is `is_admin`, which never consults the band.

    An authoring band is the *most* privileged ordinary account and still may not create
    people. Being able to write surveys has never implied deciding who answers them.
    """
    with pytest.raises(ForbiddenError):
        await require_admin(author)


async def test_it_administers_at_any_band(session):
    """`require_admin` is deliberately not layered on `require_author`.

    Administering this app is the IT function's job, not a rank: an IT operative still
    reaches the screen, which also means an administrator whose own band was edited down
    can still reach the screen that would fix it.
    """
    user = User(
        email="it2@plant.dev",
        display_name="IT Two",
        function=Function.it,
        band=Band.operative,
    )
    assert await require_admin(user) is user


# --- creating ----------------------------------------------------------------------


async def test_creating_a_floor_account_records_who_created_it(session, admin):
    created = await UserService(session).create_account(_floor(), admin)

    assert created.function is Function.production
    assert created.band is Band.operative
    assert created.created_by == admin.id


async def test_an_account_the_seed_made_has_no_creator(session, author):
    """Null means "nobody in this app created this", not a value somebody forgot.

    Every account predating the admin screen is in this state, and so is every account a
    real Microsoft sign-in will provision, because those arrive from outside the app.
    """
    assert author.created_by is None


async def test_the_hats_asked_for_are_the_hats_they_get(session, admin):
    created = await UserService(session).create_account(
        _floor(band=Band.supervisor, hats=[Hat.health_safety]), admin
    )
    assert created.hats == frozenset({Hat.health_safety})


async def test_one_job_carries_both_sides_of_a_senior_account(session, admin):
    """The successor to the author-who-is-also-on-the-floor case, now one fact rather
    than two kept in step: a shift manager authors *because* of the job that also puts
    them in the shift_managers audience."""
    created = await UserService(session).create_account(
        _floor(email="rina@plant.dev", display_name="Rina", band=Band.manager), admin
    )
    assert may_author(created)
    assert in_audience(created, SurveyAudience.shift_managers)
    assert in_audience(created, SurveyAudience.managers)


# --- the refusals ------------------------------------------------------------------


def test_half_a_job_is_unrepresentable_on_the_form():
    """The form states a job, and a job is both halves: the schema requires them, so
    the check constraint's half-job state cannot even be asked for here."""
    with pytest.raises(PydanticValidationError, match="band"):
        AccountCreate(
            email="x@plant.dev",
            display_name="X",
            function=Function.production,
        )


def test_the_same_hat_twice_is_refused():
    """The hats key is (user_id, hat), so this is otherwise an IntegrityError:
    the same refusal, several layers too late to name the field that caused it."""
    with pytest.raises(PydanticValidationError, match="twice"):
        _floor(hats=[Hat.health_safety, Hat.health_safety])


def test_the_hs_hat_on_the_hs_function_is_refused():
    """Not dangerous, just meaningless: the hat exists for people whose job is
    elsewhere, and the audience already includes the whole function. Refused so the
    directory never shows a badge that restates the job title."""
    with pytest.raises(PydanticValidationError, match="already"):
        _floor(function=Function.health_safety, band=Band.manager, hats=[Hat.health_safety])


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


async def test_an_update_removes_the_hats_it_leaves_out(session, admin):
    """The reason the update is a replacement and not a patch.

    Somebody hands the H&S duty on. A body that only ever added would make that
    unexpressible through this screen, and the account would keep a hat that decides
    which surveys reach them.
    """
    svc = UserService(session)
    created = await svc.create_account(
        _floor(band=Band.supervisor, hats=[Hat.health_safety]), admin
    )

    changed = await svc.replace_account(created.id, _update_of(_floor(band=Band.supervisor)), admin)

    assert changed.hats == frozenset()


async def test_granting_authorship_is_a_change_of_band(session, admin):
    """The answer to "who decides who can be an author": an administrator, here, by
    promoting the job. There is no role field left to set."""
    svc = UserService(session)
    created = await svc.create_account(_floor(), admin)
    assert not may_author(created)

    changed = await svc.replace_account(created.id, _update_of(_floor(band=Band.manager)), admin)

    assert may_author(changed)
    assert changed.band is Band.manager


async def test_an_absent_account_is_not_found(session, admin):
    with pytest.raises(NotFoundError):
        await UserService(session).replace_account(uuid4(), _update_of(_floor()), admin)


async def test_an_administrator_cannot_edit_away_their_own_administration(session, admin):
    """Unrecoverable from inside the app, which is what makes it worth a special case.

    The last administrator moves themselves out of IT, and from then on nobody can create
    an account or grant anybody else the function that would let them. The fix is a
    database edit, which is the thing this screen exists to stop being necessary.
    """
    with pytest.raises(ConflictError, match="your own administrator access"):
        await UserService(session).replace_account(
            admin.id,
            AccountUpdate(
                display_name="IT",
                function=Function.executive,
                band=Band.manager,
            ),
            admin,
        )


async def test_one_administrator_may_still_demote_another(session, admin):
    """Only their own account is protected. Removing somebody else's is a real thing to do."""
    svc = UserService(session)
    other = await svc.create_account(_creator(function=Function.it), admin)

    changed = await svc.replace_account(
        other.id, _update_of(_creator(function=Function.finance)), admin
    )

    assert changed.function is Function.finance


# --- signing in at all -------------------------------------------------------------


async def test_an_address_finds_the_account_whatever_its_case(session, admin):
    """The dev shim's whole sign-in, and the reason it exists.

    Listing users requires a caller, a caller is an id, and the only source of an id was
    that list. A browser with empty storage could never break in, so every page's advice
    to "pick a user in the top bar" was advice about an empty dropdown.
    """
    await UserService(session).create_account(_floor(email="rosa@plant.dev"), admin)

    found = await UserRepository(session).get_by_email("rosa@plant.dev")

    assert found is not None
    assert found.display_name == "Rosa"


async def test_an_unknown_address_finds_nobody(session):
    assert await UserRepository(session).get_by_email("nobody@plant.dev") is None


def test_identify_is_not_mounted_in_production():
    """The mount is the whole of this endpoint's protection, so it is worth a test.

    `identify` is unauthenticated of necessity: requiring a caller is the deadlock it
    undoes. Knowing an address is therefore enough to act as somebody, which is tolerable
    on a development box and not anywhere else. An endpoint that is never registered
    cannot be reached by a bug in whatever guards it, so the assertion is about the route
    table rather than about a rule.
    """
    import app.main

    # The generated schema rather than `app.routes`: an included router appears there as
    # a wrapper with no path of its own, so walking that list finds only the handful of
    # routes declared on the app itself. The schema is what is actually served.
    paths = app.main.app.openapi()["paths"]
    assert app.main.get_settings().app_env != "prod", "the suite must run as a dev box"
    assert "/api/v1/dev/identify" in paths, (
        "the suite runs with app_env=dev, so identify should be mounted here; if this "
        "fails the environment branch has moved and the frontend cannot sign in"
    )
    # The picker sits behind the same branch, and the pair moving together is the point.
    assert "/api/v1/users" in paths
    # These are not behind it, and must not drift there: without them a deployment has no
    # way to create an account and no way to know whether it is talking to an admin.
    assert "/api/v1/admin/users" in paths
    assert "/api/v1/me" in paths


def test_the_dev_surface_is_absent_when_the_app_is_built_for_production(monkeypatch):
    """The half the test above never checked, which is the half that matters.

    Its predecessor asserted only that the routes are mounted here, where APP_ENV is dev.
    That passes whether the branch exists or not, so when the branch was deleted on
    23 Aug 2026 and both routers became unconditional, nothing failed and the drift
    reached a public deployment. A guard nobody has watched reject anything is
    decoration, so this builds the app as production actually builds it and reads the
    route table back.
    """
    import importlib

    import app.main

    monkeypatch.setenv("APP_ENV", "prod")
    get_settings.cache_clear()
    try:
        production = importlib.reload(app.main)
        paths = production.app.openapi()["paths"]
        assert "/api/v1/dev/identify" not in paths, (
            "identify is unauthenticated by necessity and its mount is the whole of its "
            "protection; in production it must not be registered at all"
        )
        assert "/api/v1/dev/reset" not in paths, "production must not expose a database wipe"
        assert "/api/v1/users" not in paths, (
            "under the header shim a user id is a credential, so the list is the whole " "keyring"
        )
        # The pair that must survive the branch: without them a production deployment
        # cannot be entered or administered at all.
        assert "/api/v1/me" in paths
        assert "/api/v1/auth/me" in paths
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
        importlib.reload(app.main)


# --- what the screens read ---------------------------------------------------------


def test_me_reports_what_the_browser_could_not_work_out(admin):
    """Half of `is_admin` is an allowlist in server settings, deliberately not shipped,
    and `may_author` turns on band order, which is the server's fact. A client deciding
    either locally would decide wrongly."""
    me = MeRead(
        id=admin.id,
        display_name=admin.display_name,
        function=admin.function,
        band=admin.band,
        may_author=True,
        is_admin=True,
    )
    assert me.is_admin
    assert me.may_author


# --- reach, the number every screen must agree on ----------------------------------


async def test_reach_counts_by_the_answering_rule(session, admin):
    """One person per case, then the counts the rule implies and no others.

    Reach is live by decision, so the only thing holding every denominator honest is
    that this method asks `in_audience` rather than counting rows some other way. Note
    the admin: an IT manager holds a job now, so they are in `everyone` and `managers`,
    which is the deliberate change from the membership model, where an office account
    in no group was in no audience at all.
    """
    svc = UserService(session)
    await svc.create_account(
        _floor(email="noor@plant.dev", function=Function.quality, band=Band.operative), admin
    )
    await svc.create_account(_floor(email="rosa@plant.dev"), admin)
    await svc.create_account(
        _floor(email="rohan@plant.dev", band=Band.supervisor, hats=[Hat.health_safety]), admin
    )

    reach = await svc.reach_by_audience()

    assert reach[SurveyAudience.qa] == 1
    assert reach[SurveyAudience.operatives] == 1
    assert reach[SurveyAudience.supervisors] == 1
    assert reach[SurveyAudience.health_safety] == 1  # the hat, not the function, here
    assert reach[SurveyAudience.managers] == 1  # the IT admin's band
    assert reach[SurveyAudience.everyone] == 4  # three created, plus the admin's job
    assert SurveyAudience.person not in reach


# --- the audit log -----------------------------------------------------------------


async def test_creating_an_account_writes_its_first_history_row(session, admin):
    svc = UserService(session)
    created = await svc.create_account(_floor(), admin)

    (entry,) = await svc.history(created.id)

    assert entry.kind == "created"
    assert entry.before is None
    assert entry.after["function"] == "production"
    assert entry.after["band"] == "operative"
    assert entry.changed_by == admin.id
    assert entry.changed_by_name == admin.display_name


async def test_an_edit_records_what_it_was_and_what_it_became(session, admin):
    """The row is the answer to "why did reach move on Tuesday"."""
    svc = UserService(session)
    created = await svc.create_account(
        _floor(function=Function.quality, band=Band.operative), admin
    )

    await svc.replace_account(created.id, _update_of(_floor()), admin)

    newest, oldest = await svc.history(created.id)
    assert oldest.kind == "created"
    assert newest.kind == "updated"
    assert newest.before is not None
    assert newest.before["function"] == "quality"
    assert newest.after["function"] == "production"


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

    Noor is the only quality member and an open survey is aimed at QA, so moving her
    onto production takes that survey's reach from one to zero. The preview must say so,
    by title, with both numbers, before anything is saved.
    """
    svc = UserService(session)
    noor = await svc.create_account(
        _floor(email="noor@plant.dev", function=Function.quality), admin
    )
    session.add(_published_survey(author.id, SurveyAudience.qa, title="QA weekly"))
    await session.flush()

    impact = await svc.preview_change(noor.id, _update_of(_floor(function=Function.production)))

    assert impact.function_before is Function.quality
    assert impact.function_after is Function.production
    (survey,) = impact.surveys
    assert survey.title == "QA weekly"
    assert survey.now_in is False
    assert (survey.reach_before, survey.reach_after) == (1, 0)


async def test_preview_names_the_open_survey_a_person_would_join(session, admin, author):
    svc = UserService(session)
    rosa = await svc.create_account(_floor(), admin)
    session.add(_published_survey(author.id, SurveyAudience.qa, title="QA weekly"))
    await session.flush()

    impact = await svc.preview_change(rosa.id, _update_of(_floor(function=Function.quality)))

    (survey,) = impact.surveys
    assert survey.now_in is True
    assert (survey.reach_before, survey.reach_after) == (0, 1)


async def test_a_band_change_moves_the_managers_denominator(session, admin, author):
    """The promotion case: a band edit is what moves the manager-audience surveys now,
    the way a group edit used to move the group ones."""
    svc = UserService(session)
    rosa = await svc.create_account(_floor(), admin)
    session.add(_published_survey(author.id, SurveyAudience.managers, title="Managers monthly"))
    await session.flush()

    impact = await svc.preview_change(rosa.id, _update_of(_floor(band=Band.manager)))

    assert impact.band_before is Band.operative
    assert impact.band_after is Band.manager
    # The derived flag rides along so the dialog can warn about the authorship flip
    # without re-inventing the band cutoff client-side.
    assert (impact.may_author_before, impact.may_author_after) == (False, True)
    titles = {s.title: s.now_in for s in impact.surveys}
    assert titles["Managers monthly"] is True


async def test_a_hat_change_moves_the_health_safety_denominator(session, admin, author):
    svc = UserService(session)
    rohan = await svc.create_account(
        _floor(email="rohan@plant.dev", band=Band.supervisor, hats=[Hat.health_safety]), admin
    )
    session.add(_published_survey(author.id, SurveyAudience.health_safety, title="H&S check"))
    await session.flush()

    impact = await svc.preview_change(rohan.id, _update_of(_floor(band=Band.supervisor)))

    assert impact.hats_removed == [Hat.health_safety]
    (survey,) = impact.surveys
    assert survey.title == "H&S check"
    assert survey.now_in is False


async def test_preview_is_silent_about_surveys_the_edit_does_not_touch(session, admin, author):
    """The job is unchanged for the operatives audience, so the operatives survey must
    not appear: a preview that lists everything teaches admins to read none of it."""
    svc = UserService(session)
    rosa = await svc.create_account(_floor(), admin)
    session.add(_published_survey(author.id, SurveyAudience.operatives, title="Ops daily"))
    await session.flush()

    impact = await svc.preview_change(rosa.id, _update_of(_floor(display_name="Renamed")))

    assert impact.surveys == []


async def test_preview_skips_drafts_and_closed_surveys(session, admin, author):
    """Only open surveys are guarded: a draft reaches nobody yet, and a closed survey
    takes no new answers, so neither has a denominator this edit can move.

    Noor flips out of the QA audience here, and the preview must still be empty,
    because the only QA surveys that exist are a draft and a closed one.
    """
    svc = UserService(session)
    noor = await svc.create_account(
        _floor(email="noor@plant.dev", function=Function.quality), admin
    )
    draft = _published_survey(author.id, SurveyAudience.qa, title="Draft")
    draft.status = TemplateStatus.draft
    closed = _published_survey(author.id, SurveyAudience.qa, title="Closed")
    closed.status = TemplateStatus.closed
    session.add(draft)
    session.add(closed)
    await session.flush()

    impact = await svc.preview_change(noor.id, _update_of(_floor(function=Function.production)))

    assert impact.function_after is Function.production
    assert impact.surveys == []


async def test_preview_never_reports_a_survey_aimed_at_one_person(session, admin, author):
    """The target is an id: no change of job makes this user someone else, so a
    person-aimed survey cannot flip and must never show up as if it could."""
    svc = UserService(session)
    rosa = await svc.create_account(_floor(), admin)
    session.add(
        _published_survey(author.id, SurveyAudience.person, title="Just Rosa", target=rosa.id)
    )
    await session.flush()

    impact = await svc.preview_change(rosa.id, _update_of(_floor(band=Band.line_leader)))

    assert impact.surveys == []


async def test_preview_writes_nothing(session, admin, author):
    """Read-only by construction, asserted anyway: a what-if that saved would be the
    exact bug its name promises it is not."""
    svc = UserService(session)
    noor = await svc.create_account(
        _floor(email="noor@plant.dev", function=Function.quality), admin
    )

    await svc.preview_change(noor.id, _update_of(_floor(function=Function.production)))

    fresh = await UserRepository(session).get(noor.id)
    assert fresh is not None
    assert fresh.function is Function.quality
    entries = await svc.history(noor.id)
    assert [e.kind for e in entries] == ["created"]


async def test_preview_of_an_absent_account_is_not_found(session, admin):
    with pytest.raises(NotFoundError):
        await UserService(session).preview_change(uuid4(), _update_of(_floor()))
