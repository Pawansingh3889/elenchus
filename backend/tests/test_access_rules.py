"""The access rules, exhaustively and without a database.

app/access holds pure functions over values, which is what makes this affordable: every
combination of who is asking and what they are asking about, checked directly, with no
fixtures and no session. The matrix is the point. A rule with one untested corner is a
rule nobody can safely change.

Reading these, the shapes to hold onto:

* Everything derives from the job. One (function, band) pair per person, plus hats;
  there is no stored role, no membership rows, and no way to record a line leader who
  is also QA.
* Authoring is a band (manager and up), asked through `may_author`, never stored.
* Answering and reading are different questions. Being in a survey's audience means you
  were asked. It does not mean you may read what your colleagues answered.
* Colleagues are the authoring bands of one function, symmetric; the executive function
  reads everything and edits nothing.
"""

from uuid import UUID, uuid4

import pytest

from app.access import (
    NOBODY,
    in_audience,
    may_answer,
    may_author,
    may_edit,
    may_list,
    may_read_rows,
    may_read_totals,
    reads_all_surveys,
)
from app.access.rules import is_admin
from app.roles.models import Permission, Role, RolePermission, UserRole
from app.templates.enums import SurveyAudience
from app.users.models import Band, Function, Hat, User, UserHat

AUTHOR_ID = uuid4()
OTHER_ID = uuid4()


def _user(
    function: Function | None = None,
    band: Band | None = None,
    hats: tuple[Hat, ...] = (),
    **kw,
) -> User:
    user = User(
        id=kw.get("id", uuid4()),
        email=kw.get("email", "someone@test.dev"),
        display_name="Test",
        function=function,
        band=band,
    )
    # Assigned rather than passed to the constructor so `hats` stays a property over the
    # rows: one source of truth, and no way for a test to set up a user the database could
    # not produce.
    user.hat_rows = [UserHat(user_id=user.id, hat=h) for h in hats]
    return user


def _with_role(user: User, *permissions: Permission, name: str = "Test Role") -> User:
    """The same user, carrying one role that bundles the given permissions.

    Built the way `_user` builds hats: assigned rows in memory rather than written and
    read back, so the rule is exercised directly and no test here needs a database.
    """
    role = Role(name=name, permission_rows=[RolePermission(permission=p) for p in permissions])
    user.role_rows = [UserRole(user_id=user.id, role=role)]
    return user


AUTHOR = _user(Function.hr, Band.manager, id=AUTHOR_ID, email="author@test.dev")
# The case the whole model exists for: somebody who authors from the floor.
SHIFT_MANAGER = _user(Function.production, Band.manager)
OPERATIVE = _user(Function.production, Band.operative)
LINE_LEADER = _user(Function.production, Band.line_leader)
# A supervisor with additional H&S responsibility: the job stays production, the duty
# is a hat.
SUPERVISOR_HS = _user(Function.production, Band.supervisor, (Hat.health_safety,))
HS_MANAGER = _user(Function.health_safety, Band.manager)
QA_FLOOR = _user(Function.quality, Band.operative)
QA_HEAD = _user(Function.quality, Band.head)
JOBLESS = _user(None, None)
HR_COLLEAGUE = _user(Function.hr, Band.manager)
# Same function as the author, below the authoring bands: sees nothing, reads nothing.
HR_JUNIOR = _user(Function.hr, Band.supervisor)
FINANCE = _user(Function.finance, Band.manager)
EXECUTIVE = _user(Function.executive, Band.head)
TARGET = _user(Function.production, Band.operative)


# --------------------------------------------------------------------------- authoring


@pytest.mark.parametrize(
    "user,expected",
    [
        (OPERATIVE, False),
        (LINE_LEADER, False),
        (SUPERVISOR_HS, False),
        (SHIFT_MANAGER, True),
        (QA_HEAD, True),
        (EXECUTIVE, True),
        (JOBLESS, False),
    ],
)
def test_authoring_is_the_manager_band_and_up(user, expected):
    """The stored role column is gone; this derivation is what replaced it."""
    assert may_author(user) is expected


# ----------------------------------------------------------------------------- answering


@pytest.mark.parametrize(
    "user,audience,admin,expected",
    [
        # The production ladder, band by band.
        (OPERATIVE, SurveyAudience.operatives, False, True),
        (OPERATIVE, SurveyAudience.supervisors, False, False),
        (LINE_LEADER, SurveyAudience.line_leaders, False, True),
        (SUPERVISOR_HS, SurveyAudience.supervisors, False, True),
        (SHIFT_MANAGER, SurveyAudience.shift_managers, False, True),
        # shift_managers is production/manager, not manager-anywhere: an HR manager and
        # the head of QA are not shift managers.
        (HR_COLLEAGUE, SurveyAudience.shift_managers, False, False),
        (QA_HEAD, SurveyAudience.shift_managers, False, False),
        # qa is the whole quality ladder, floor to head.
        (QA_FLOOR, SurveyAudience.qa, False, True),
        (QA_HEAD, SurveyAudience.qa, False, True),
        (OPERATIVE, SurveyAudience.qa, False, False),
        # health_safety is the function or the hat.
        (HS_MANAGER, SurveyAudience.health_safety, False, True),
        (SUPERVISOR_HS, SurveyAudience.health_safety, False, True),
        (OPERATIVE, SurveyAudience.health_safety, False, False),
        # managers is a band across functions, which is what the word means here.
        (SHIFT_MANAGER, SurveyAudience.managers, False, True),
        (AUTHOR, SurveyAudience.managers, False, True),
        (QA_HEAD, SurveyAudience.managers, False, True),
        (EXECUTIVE, SurveyAudience.managers, False, True),
        (SUPERVISOR_HS, SurveyAudience.managers, False, False),
        # Everyone means everyone with a job, whatever kind of account they hold.
        (OPERATIVE, SurveyAudience.everyone, False, True),
        (SHIFT_MANAGER, SurveyAudience.everyone, False, True),
        (FINANCE, SurveyAudience.everyone, False, True),
        # And not an account belonging to nobody on any ladder.
        (JOBLESS, SurveyAudience.everyone, False, False),
        (JOBLESS, SurveyAudience.operatives, False, False),
        # Admin reaches everything, and so does the survey's own author.
        (FINANCE, SurveyAudience.operatives, True, True),
        (AUTHOR, SurveyAudience.qa, False, True),
    ],
)
def test_who_may_answer(user, audience, admin, expected):
    assert bool(may_answer(user, audience, AUTHOR_ID, admin)) is expected


def test_one_job_per_person_keeps_qa_and_production_apart():
    """The separation-of-duty property, stated as its own test because it is the flaw
    that forced the job model: the old membership table happily recorded a line leader
    who was also QA. A line leader is not in the qa audience, a floor QA is not in any
    production audience, and there is no way to build a User who is both."""
    assert not may_answer(LINE_LEADER, SurveyAudience.qa, OTHER_ID, admin=False)
    assert not may_answer(QA_FLOOR, SurveyAudience.line_leaders, OTHER_ID, admin=False)
    assert not may_answer(QA_FLOOR, SurveyAudience.operatives, OTHER_ID, admin=False)


def test_holding_an_authoring_band_does_not_change_what_you_are_asked():
    """The successor to 'role is not consulted': the people in senior jobs author
    surveys, and are still asked the surveys aimed at their own job."""
    assert may_answer(SHIFT_MANAGER, SurveyAudience.shift_managers, OTHER_ID, admin=False)
    assert may_answer(QA_HEAD, SurveyAudience.qa, OTHER_ID, admin=False)
    assert may_answer(HS_MANAGER, SurveyAudience.health_safety, OTHER_ID, admin=False)


# ------------------------------------------------------------------- one named person


def test_a_survey_for_one_person_reaches_only_that_person():
    assert may_answer(TARGET, SurveyAudience.person, OTHER_ID, False, target=TARGET.id)
    assert not may_answer(OPERATIVE, SurveyAudience.person, OTHER_ID, False, target=TARGET.id)
    # Sharing their job is no help: the audience is a person, not a job.
    assert not may_answer(LINE_LEADER, SurveyAudience.person, OTHER_ID, False, target=TARGET.id)


def test_a_survey_for_a_person_who_was_never_named_reaches_nobody():
    """Fails closed and says which half is missing. A `person` row with no id cannot be
    answered by anyone, and reading it as "for everybody" would be the dangerous guess."""
    decision = may_answer(TARGET, SurveyAudience.person, OTHER_ID, False, target=None)
    assert not decision
    assert "names nobody" in decision.reason


def test_the_author_and_an_admin_still_reach_a_personal_survey():
    """Same two escape hatches as every other audience: an author has to be able to try
    what they built, and an admin has to be able to look."""
    assert may_answer(AUTHOR, SurveyAudience.person, AUTHOR_ID, False, target=TARGET.id)
    assert may_answer(FINANCE, SurveyAudience.person, OTHER_ID, True, target=TARGET.id)


def test_a_survey_with_no_audience_is_answerable_by_nobody():
    """Fails closed. The dangerous failure is not a refusal, it is a survey reaching
    people it was never aimed at."""
    for user in (OPERATIVE, SHIFT_MANAGER, FINANCE, AUTHOR):
        assert not may_answer(user, None, AUTHOR_ID, admin=False)


def test_a_refusal_says_which_piece_was_missing():
    """A bare False is enough to enforce the rule and useless to fix a deployment."""
    jobless = may_answer(JOBLESS, SurveyAudience.everyone, OTHER_ID, False)
    wrong_band = may_answer(OPERATIVE, SurveyAudience.supervisors, OTHER_ID, False)
    assert "no job" in jobless.reason
    assert "no audience" in may_answer(OPERATIVE, None, OTHER_ID, False).reason
    assert "supervisor" in wrong_band.reason


# ------------------------------------------------------------------------------- reading


@pytest.mark.parametrize(
    "user,admin,expected",
    [
        (AUTHOR, False, True),
        (HR_COLLEAGUE, True, True),
        # A colleague at authoring band in the author's function.
        (HR_COLLEAGUE, False, True),
        # Same function, below the authoring bands: the line that keeps a function's
        # floor out of its seniors' results.
        (HR_JUNIOR, False, False),
        (FINANCE, False, False),
        (OPERATIVE, False, False),
        # Site leadership reads everything.
        (EXECUTIVE, False, True),
    ],
)
def test_who_may_read_individual_rows(user, admin, expected):
    assert bool(may_read_rows(user, AUTHOR_ID, admin, creator_function=Function.hr)) is expected


def test_two_people_without_a_function_are_not_colleagues():
    """The bug this rules out is a one-character one. `None is None` is true, so a rule
    that compared functions without checking for one would make every person without a
    job a colleague of every other and hand them each other's answers."""
    assert not may_read_rows(JOBLESS, AUTHOR_ID, False, creator_function=None)
    assert not may_read_rows(OPERATIVE, AUTHOR_ID, False, creator_function=None)


def test_being_in_the_audience_does_not_let_you_read_the_rows():
    """The distinction the whole design rests on. An operative may answer a survey aimed
    at operatives and may see its totals, and may not read what their colleagues said."""
    assert may_answer(OPERATIVE, SurveyAudience.operatives, OTHER_ID, admin=False)
    assert may_read_totals(OPERATIVE, SurveyAudience.operatives, OTHER_ID, admin=False)
    assert not may_read_rows(OPERATIVE, OTHER_ID, admin=False)


def test_the_target_functions_seniors_do_not_read_the_rows():
    """Decided deliberately: HR surveying the QA team does not hand head QA the raw
    answers, or nobody could survey a team candidly about its own management. Findings
    travel by a person choosing to share them, not by access."""
    assert not may_read_rows(QA_HEAD, AUTHOR_ID, False, creator_function=Function.hr)


@pytest.mark.parametrize(
    "user,audience,expected",
    [
        (OPERATIVE, SurveyAudience.operatives, True),
        (FINANCE, SurveyAudience.operatives, False),
        (LINE_LEADER, SurveyAudience.everyone, True),
        (JOBLESS, SurveyAudience.everyone, False),
    ],
)
def test_who_may_read_totals(user, audience, expected):
    assert bool(may_read_totals(user, audience, OTHER_ID, admin=False)) is expected


# ------------------------------------------------------------------------------- listing


def test_a_survey_you_cannot_answer_is_not_even_named_to_you():
    """Existence is information: 'Redundancy consultation' says something before a single
    answer is given."""
    assert not may_list(FINANCE, SurveyAudience.operatives, OTHER_ID, admin=False)
    assert may_list(OPERATIVE, SurveyAudience.operatives, OTHER_ID, admin=False)
    assert may_list(FINANCE, SurveyAudience.operatives, OTHER_ID, admin=True)


def test_a_function_colleague_sees_the_survey():
    """Asked for so that work does not stop when the person who made it is away, and
    silo'd by function: finance does not see HR's surveys, and HR's own junior bands do
    not see them either."""
    assert may_list(
        HR_COLLEAGUE,
        SurveyAudience.operatives,
        AUTHOR_ID,
        admin=False,
        creator_function=Function.hr,
    )
    assert not may_list(
        FINANCE,
        SurveyAudience.operatives,
        AUTHOR_ID,
        admin=False,
        creator_function=Function.hr,
    )
    assert not may_list(
        HR_JUNIOR,
        SurveyAudience.managers,
        AUTHOR_ID,
        admin=False,
        creator_function=Function.hr,
    )


def test_an_author_always_sees_their_own_work():
    """Even aimed at a group they are not in, or with no audience at all, or they could
    create something and lose it."""
    assert may_list(AUTHOR, SurveyAudience.operatives, AUTHOR_ID, admin=False)
    assert may_list(AUTHOR, None, AUTHOR_ID, admin=False)


# ----------------------------------------------------------------------------- executive


def test_the_executive_reads_everything_and_edits_nothing():
    """Site leadership oversight, exactly that wide and no wider. The factory manager
    sees every survey and its rows, and cannot change a word of any of them."""
    assert reads_all_surveys(EXECUTIVE)
    assert may_list(EXECUTIVE, SurveyAudience.operatives, AUTHOR_ID, admin=False)
    assert may_read_rows(EXECUTIVE, AUTHOR_ID, False, creator_function=Function.hr)
    assert not may_edit(EXECUTIVE, AUTHOR_ID, admin=False)


def test_reads_everything_needs_the_band_as_well_as_the_function():
    """`executive` at a floor band is a data-entry mistake, not a licence: the predicate
    asks for the authoring bands, so the mistake grants nothing."""
    assert not reads_all_surveys(_user(Function.executive, Band.operative))
    assert not reads_all_surveys(QA_HEAD)


def test_oversight_does_not_put_leadership_in_every_denominator():
    """The executive reads an operatives survey and is not counted in its reach: reach
    counts who a survey was written for, and oversight is not membership."""
    assert not in_audience(EXECUTIVE, SurveyAudience.operatives)
    assert in_audience(EXECUTIVE, SurveyAudience.managers)


# --------------------------------------------------------------------------------- admin


def test_admin_comes_from_the_allowlist_and_ignores_case():
    allowlist = frozenset({"Boss@Example.com"})
    assert is_admin(_user(Function.hr, Band.manager, email="boss@example.com"), allowlist)
    assert not is_admin(_user(Function.hr, Band.manager, email="someone@example.com"), allowlist)


def test_an_empty_allowlist_grants_nobody():
    assert not is_admin(AUTHOR, frozenset())


def test_the_it_function_grants_admin():
    """The reversal, tested so it is deliberate rather than incidental: a column now
    confers administration, where the older rule kept that strictly in configuration.
    Any band of IT, because administering this app is the department's job, not a rank."""
    assert is_admin(_user(Function.it, Band.operative), frozenset())
    assert is_admin(_user(Function.it, Band.manager), frozenset())
    assert not is_admin(_user(Function.executive, Band.director), frozenset())


# ------------------------------------------------- roles: additive beyond the job


def test_a_granted_survey_author_permission_makes_a_jobless_account_an_author():
    granted = _with_role(_user(None, None, id=uuid4()), Permission.survey_author)
    assert may_author(granted)


def test_a_role_alone_reaches_no_further_than_the_permission_it_carries():
    """Granting `survey_author` does not also grant admin, or anything else nobody
    listed: additive means the union of what is named, never a bundle of everything a
    manager band happens to imply elsewhere."""
    granted = _with_role(_user(None, None, id=uuid4()), Permission.survey_author)
    assert not is_admin(granted, frozenset())
    assert not may_edit(granted, created_by=AUTHOR_ID, admin=False)


def test_a_role_can_grant_full_administration():
    granted = _with_role(_user(None, None, id=uuid4()), Permission.admin_all)
    assert is_admin(granted, frozenset())


def test_a_role_can_grant_editing_a_survey_that_is_not_ones_own():
    granted = _with_role(_user(None, None, id=uuid4()), Permission.survey_edit)
    assert may_edit(granted, created_by=AUTHOR_ID, admin=False)


def test_a_role_can_grant_reading_rows_across_every_survey():
    """The shape a custom "Survey Auditor" role takes: nobody's colleague, no band, and
    still able to read what respondents said."""
    auditor = _with_role(_user(None, None, id=uuid4()), Permission.results_read_rows)
    assert may_read_rows(auditor, created_by=AUTHOR_ID, admin=False)


def test_a_role_grant_of_totals_does_not_imply_rows():
    granted = _with_role(_user(None, None, id=uuid4()), Permission.results_read_totals)
    assert not may_read_rows(granted, created_by=AUTHOR_ID, admin=False)
    assert may_read_totals(granted, SurveyAudience.everyone, created_by=AUTHOR_ID, admin=False)


def test_a_role_can_grant_seeing_every_survey_in_listings():
    granted = _with_role(_user(None, None, id=uuid4()), Permission.survey_list)
    assert may_list(granted, SurveyAudience.qa, created_by=AUTHOR_ID, admin=False)


def test_no_role_is_the_same_as_no_extra_grant():
    """An account with no roles reads exactly as one built before `app.roles` existed:
    `granted_permissions` is empty, not merely absent."""
    plain = _user(Function.production, Band.operative)
    assert plain.granted_permissions == frozenset()
    assert not may_edit(plain, created_by=AUTHOR_ID, admin=False)


# ------------------------------------------------------------------- completeness


CAST = [
    AUTHOR,
    SHIFT_MANAGER,
    OPERATIVE,
    LINE_LEADER,
    SUPERVISOR_HS,
    HS_MANAGER,
    QA_FLOOR,
    QA_HEAD,
    JOBLESS,
    HR_COLLEAGUE,
    HR_JUNIOR,
    FINANCE,
    EXECUTIVE,
]


def test_every_audience_has_a_membership_rule():
    """The failure this exists for is silent and fatal: an audience added to the enum
    without a derivation would refuse everyone with the fallback reason, and the first
    sign would be a survey nobody can answer. Every audience except `person` must admit
    at least one member of a cast that covers every ladder."""
    for audience in SurveyAudience:
        if audience is SurveyAudience.person:
            continue
        assert any(
            in_audience(user, audience) for user in CAST
        ), f"no cast member is in audience {audience.value}"


def test_no_audience_and_cast_combination_raises():
    """The whole matrix, evaluated. A KeyError here is an audience half-added."""
    for audience in SurveyAudience:
        for user in CAST:
            may_answer(user, audience, OTHER_ID, admin=False, target=TARGET.id)


def test_reach_counts_the_audience_and_not_the_ways_around_it():
    """`in_audience` is the denominator's rule, and a denominator must count the people a
    survey was written for. The author testing their own survey and an admin reaching in
    are how it gets answered by someone it was not aimed at, so neither is counted."""
    # The author owns nothing here: NOBODY can match no user, so the owner branch is shut.
    assert in_audience(OPERATIVE, SurveyAudience.operatives)
    assert not in_audience(FINANCE, SurveyAudience.operatives)
    assert not in_audience(JOBLESS, SurveyAudience.everyone)


def test_reach_for_one_person_is_that_person_alone():
    assert in_audience(TARGET, SurveyAudience.person, target=TARGET.id)
    assert not in_audience(OPERATIVE, SurveyAudience.person, target=TARGET.id)


def test_nobody_is_nobody(author, respondent):
    """The sentinel only works while no real user carries it. The seeded ids are
    00000000-0000-0000-0000-0000000000a1-shaped, which is close enough to check."""
    assert NOBODY == UUID(int=0)
    assert author.id != NOBODY
    assert respondent.id != NOBODY
