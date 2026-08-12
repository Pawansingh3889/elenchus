"""The access rules, exhaustively and without a database.

app/access holds pure functions over values, which is what makes this affordable: every
combination of who is asking and what they are asking about, checked directly, with no
fixtures and no session. The matrix is the point. A rule with one untested corner is a
rule nobody can safely change.

Reading these, the shapes to hold onto:

* Answering is decided by group membership, never by `role`. The senior groups are full
  of people who sign in with Teams and therefore hold author accounts.
* Answering and reading are different questions. Being in a survey's audience means you
  were asked. It does not mean you may read what your colleagues answered.
* Departments group authors, and a department colleague may now read the rows.
"""

from uuid import UUID, uuid4

import pytest

from app.access import NOBODY, in_audience, may_answer, may_list, may_read_rows, may_read_totals
from app.access.rules import is_admin
from app.templates.enums import SurveyAudience
from app.users.models import (
    CreatorDepartment,
    RespondentGroup,
    User,
    UserGroupMembership,
    UserRole,
)

AUTHOR_ID = uuid4()
OTHER_ID = uuid4()


def _user(
    role: UserRole,
    department: CreatorDepartment | None = None,
    groups: tuple[RespondentGroup, ...] = (),
    **kw,
) -> User:
    user = User(
        id=kw.get("id", uuid4()),
        email=kw.get("email", "someone@test.dev"),
        display_name="Test",
        role=role,
        department=department,
    )
    # Assigned rather than passed to the constructor so `groups` stays a property over the
    # rows: one source of truth, and no way for a test to set up a user the database could
    # not produce.
    user.memberships = [UserGroupMembership(user_id=user.id, group=g) for g in groups]
    return user


AUTHOR = _user(
    UserRole.author,
    CreatorDepartment.hr,
    (RespondentGroup.managers,),
    id=AUTHOR_ID,
    email="author@test.dev",
)
# The case the whole model exists for: an author account whose holder works on the line.
SUPERVISOR_AUTHOR = _user(UserRole.author, CreatorDepartment.hr, (RespondentGroup.supervisors,))
OPERATIVE = _user(UserRole.respondent, None, (RespondentGroup.operatives,))
# In two groups at once, which a single column could not have expressed.
LINE_LEADER_QA = _user(
    UserRole.respondent, None, (RespondentGroup.line_leaders, RespondentGroup.qa)
)
UNGROUPED = _user(UserRole.respondent, None, ())
HR_COLLEAGUE = _user(UserRole.author, CreatorDepartment.hr)
FINANCE = _user(UserRole.author, CreatorDepartment.finance)
TARGET = _user(UserRole.respondent, None, (RespondentGroup.operatives,))


# ----------------------------------------------------------------------------- answering


@pytest.mark.parametrize(
    "user,audience,admin,expected",
    [
        # A group survey is for that group's members.
        (OPERATIVE, SurveyAudience.operatives, False, True),
        (OPERATIVE, SurveyAudience.supervisors, False, False),
        (LINE_LEADER_QA, SurveyAudience.line_leaders, False, True),
        # Both of them, because membership is a set and not a column.
        (LINE_LEADER_QA, SurveyAudience.qa, False, True),
        # The point of the rewrite: an author account in the group may answer. Under the
        # old rule this was refused for being a creator, which refused every supervisor a
        # survey written for supervisors.
        (SUPERVISOR_AUTHOR, SurveyAudience.supervisors, False, True),
        (SUPERVISOR_AUTHOR, SurveyAudience.operatives, False, False),
        # Everyone means everyone on the floor, whatever kind of account they hold.
        (OPERATIVE, SurveyAudience.everyone, False, True),
        (SUPERVISOR_AUTHOR, SurveyAudience.everyone, False, True),
        # And not an account belonging to nobody on the floor.
        (UNGROUPED, SurveyAudience.everyone, False, False),
        (UNGROUPED, SurveyAudience.operatives, False, False),
        # Admin reaches everything, and so does the survey's own author.
        (FINANCE, SurveyAudience.operatives, True, True),
        (AUTHOR, SurveyAudience.qa, False, True),
    ],
)
def test_who_may_answer(user, audience, admin, expected):
    assert bool(may_answer(user, audience, AUTHOR_ID, admin)) is expected


def test_role_is_not_consulted_when_deciding_who_may_answer():
    """Stated as its own test because it is the rule that changed and the one most likely
    to be quietly reinstated by someone tidying up. A respondent and an author who are in
    the same group get the same answer."""
    author_side = _user(UserRole.author, CreatorDepartment.hr, (RespondentGroup.qa,))
    respondent_side = _user(UserRole.respondent, None, (RespondentGroup.qa,))
    for user in (author_side, respondent_side):
        assert may_answer(user, SurveyAudience.qa, OTHER_ID, admin=False)


# ------------------------------------------------------------------- one named person


def test_a_survey_for_one_person_reaches_only_that_person():
    assert may_answer(TARGET, SurveyAudience.person, OTHER_ID, False, target=TARGET.id)
    assert not may_answer(OPERATIVE, SurveyAudience.person, OTHER_ID, False, target=TARGET.id)
    # Being in a group is no help: the audience is a person, not a group.
    assert not may_answer(LINE_LEADER_QA, SurveyAudience.person, OTHER_ID, False, target=TARGET.id)


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
    for user in (OPERATIVE, SUPERVISOR_AUTHOR, FINANCE, AUTHOR):
        assert not may_answer(user, None, AUTHOR_ID, admin=False)


def test_a_refusal_says_which_piece_was_missing():
    """A bare False is enough to enforce the rule and useless to fix a deployment."""
    ungrouped = may_answer(UNGROUPED, SurveyAudience.everyone, OTHER_ID, False)
    wrong_group = may_answer(OPERATIVE, SurveyAudience.supervisors, OTHER_ID, False)
    assert "not in any group" in ungrouped.reason
    assert "no audience" in may_answer(OPERATIVE, None, OTHER_ID, False).reason
    assert "supervisors" in wrong_group.reason


# ------------------------------------------------------------------------------- reading


@pytest.mark.parametrize(
    "user,admin,expected",
    [
        (AUTHOR, False, True),
        (HR_COLLEAGUE, True, True),
        # A colleague in the author's department, which is the new grant.
        (HR_COLLEAGUE, False, True),
        (FINANCE, False, False),
        (OPERATIVE, False, False),
    ],
)
def test_who_may_read_individual_rows(user, admin, expected):
    assert (
        bool(may_read_rows(user, AUTHOR_ID, admin, creator_department=CreatorDepartment.hr))
        is expected
    )


def test_two_people_without_a_department_are_not_colleagues():
    """The bug this rules out is a one-character one. `None is None` is true, so a rule
    that compared departments without checking for one would make every person on the
    floor a colleague of every other and hand them each other's answers."""
    assert not may_read_rows(UNGROUPED, AUTHOR_ID, False, creator_department=None)
    assert not may_read_rows(OPERATIVE, AUTHOR_ID, False, creator_department=None)


def test_being_in_the_audience_does_not_let_you_read_the_rows():
    """The distinction the whole design rests on. An operative may answer a survey aimed
    at operatives and may see its totals, and may not read what their colleagues said."""
    assert may_answer(OPERATIVE, SurveyAudience.operatives, OTHER_ID, admin=False)
    assert may_read_totals(OPERATIVE, SurveyAudience.operatives, OTHER_ID, admin=False)
    assert not may_read_rows(OPERATIVE, OTHER_ID, admin=False)


@pytest.mark.parametrize(
    "user,audience,expected",
    [
        (OPERATIVE, SurveyAudience.operatives, True),
        (FINANCE, SurveyAudience.operatives, False),
        (LINE_LEADER_QA, SurveyAudience.everyone, True),
        (UNGROUPED, SurveyAudience.everyone, False),
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


def test_a_department_colleague_sees_the_survey():
    """Asked for so that work does not stop when the person who made it is away."""
    assert may_list(
        HR_COLLEAGUE,
        SurveyAudience.operatives,
        AUTHOR_ID,
        admin=False,
        creator_department=CreatorDepartment.hr,
    )
    assert not may_list(
        FINANCE,
        SurveyAudience.operatives,
        AUTHOR_ID,
        admin=False,
        creator_department=CreatorDepartment.hr,
    )


def test_an_author_always_sees_their_own_work():
    """Even aimed at a group they are not in, or with no audience at all, or they could
    create something and lose it."""
    assert may_list(AUTHOR, SurveyAudience.operatives, AUTHOR_ID, admin=False)
    assert may_list(AUTHOR, None, AUTHOR_ID, admin=False)


# --------------------------------------------------------------------------------- admin


def test_admin_comes_from_the_allowlist_and_ignores_case():
    allowlist = frozenset({"Boss@Example.com"})
    assert is_admin(_user(UserRole.author, email="boss@example.com"), allowlist)
    assert not is_admin(_user(UserRole.author, email="someone@example.com"), allowlist)


def test_an_empty_allowlist_grants_nobody():
    assert not is_admin(AUTHOR, frozenset())


def test_the_it_department_grants_admin():
    """The reversal, tested so it is deliberate rather than incidental: a column now
    confers administration, where the older rule kept that strictly in configuration."""
    assert is_admin(_user(UserRole.author, CreatorDepartment.it), frozenset())
    assert not is_admin(_user(UserRole.author, CreatorDepartment.management), frozenset())


# ------------------------------------------------------------------- completeness


def test_every_group_audience_maps_to_a_group():
    """The failure this exists for is silent and fatal. `may_answer` looks the audience up
    in `_AUDIENCE_GROUP` with no fallback, so an audience added to the enum without a
    matching entry does not refuse anyone: it raises KeyError the first time somebody
    opens that survey. Enumerating the enum means the next group cannot be half-added.

    `everyone` and `person` are excluded deliberately. Neither is a group.
    """
    from app.access.rules import _AUDIENCE_GROUP

    grouped = {
        a for a in SurveyAudience if a not in (SurveyAudience.everyone, SurveyAudience.person)
    }
    assert grouped == set(_AUDIENCE_GROUP), "every group audience needs an entry in _AUDIENCE_GROUP"


def test_every_group_can_be_aimed_at():
    """A group nobody can survey is a group that only half exists."""
    assert {g.value for g in RespondentGroup} <= {a.value for a in SurveyAudience}


def test_reach_counts_the_audience_and_not_the_ways_around_it():
    """`in_audience` is the denominator's rule, and a denominator must count the people a
    survey was written for. The author testing their own survey and an admin reaching in
    are how it gets answered by someone it was not aimed at, so neither is counted."""
    # The author owns nothing here: NOBODY can match no user, so the owner branch is shut.
    assert in_audience(OPERATIVE, SurveyAudience.operatives)
    assert not in_audience(FINANCE, SurveyAudience.operatives)
    assert not in_audience(UNGROUPED, SurveyAudience.everyone)


def test_reach_for_one_person_is_that_person_alone():
    assert in_audience(TARGET, SurveyAudience.person, target=TARGET.id)
    assert not in_audience(OPERATIVE, SurveyAudience.person, target=TARGET.id)


def test_nobody_is_nobody(author, respondent):
    """The sentinel only works while no real user carries it. The seeded ids are
    00000000-0000-0000-0000-0000000000a1-shaped, which is close enough to check."""
    assert NOBODY == UUID(int=0)
    assert author.id != NOBODY
    assert respondent.id != NOBODY
