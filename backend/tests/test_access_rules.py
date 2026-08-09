"""The access rules, exhaustively and without a database.

app/access holds pure functions over values, which is what makes this affordable: every
combination of who is asking and what they are asking about, checked directly, with no
fixtures and no session. The matrix is the point. A rule with one untested corner is a
rule nobody can safely change.

Reading these, the shape to hold onto is that answering and reading are different
questions. Being in a survey's audience means you were asked. It does not mean you may
read what your colleagues answered.
"""

from uuid import uuid4

import pytest

from app.access import may_answer, may_list, may_read_rows, may_read_totals
from app.access.rules import is_admin
from app.templates.enums import SurveyAudience
from app.users.models import CreatorDepartment, User, UserRole

AUTHOR_ID = uuid4()
OTHER_ID = uuid4()


def _user(role: UserRole, department: CreatorDepartment | None = None, **kw) -> User:
    return User(
        id=kw.get("id", uuid4()),
        email=kw.get("email", "someone@test.dev"),
        display_name="Test",
        role=role,
        department=department,
    )


AUTHOR = _user(UserRole.author, CreatorDepartment.hr, id=AUTHOR_ID, email="author@test.dev")
HR = _user(UserRole.author, CreatorDepartment.hr)
FINANCE = _user(UserRole.author, CreatorDepartment.finance)
TECHNICAL = _user(UserRole.author, CreatorDepartment.technical)
NO_DEPARTMENT = _user(UserRole.author, None)
RESPONDENT = _user(UserRole.respondent)


# ----------------------------------------------------------------------------- answering


@pytest.mark.parametrize(
    "user,audience,admin,expected",
    [
        # A respondent-aimed survey is for respondents, and for its author testing it.
        (RESPONDENT, SurveyAudience.respondents, False, True),
        (HR, SurveyAudience.respondents, False, False),
        (AUTHOR, SurveyAudience.respondents, False, True),
        # A department survey is for that department. Being a creator is not enough.
        (HR, SurveyAudience.hr, False, True),
        (FINANCE, SurveyAudience.hr, False, False),
        (RESPONDENT, SurveyAudience.hr, False, False),
        # Admin reaches everything, and so does the survey's own author.
        (FINANCE, SurveyAudience.hr, True, True),
        (AUTHOR, SurveyAudience.finance, False, True),
        # Technical, the fifth department, behaves like the rest of them.
        (TECHNICAL, SurveyAudience.technical, False, True),
        (HR, SurveyAudience.technical, False, False),
        # Fails closed: no department cannot be matched to any audience.
        (NO_DEPARTMENT, SurveyAudience.hr, False, False),
    ],
)
def test_who_may_answer(user, audience, admin, expected):
    assert bool(may_answer(user, audience, AUTHOR_ID, admin)) is expected


def test_a_survey_with_no_audience_is_answerable_by_nobody():
    """Fails closed. The dangerous failure is not a refusal, it is a survey reaching
    people it was never aimed at."""
    for user in (RESPONDENT, HR, FINANCE, AUTHOR):
        assert not may_answer(user, None, AUTHOR_ID, admin=False)


def test_a_refusal_says_which_piece_was_missing():
    """A bare False is enough to enforce the rule and useless to fix a deployment."""
    assert "no department" in may_answer(NO_DEPARTMENT, SurveyAudience.hr, OTHER_ID, False).reason
    assert "no audience" in may_answer(HR, None, OTHER_ID, False).reason
    assert "hr team" in may_answer(FINANCE, SurveyAudience.hr, OTHER_ID, False).reason


# ------------------------------------------------------------------------------- reading


@pytest.mark.parametrize(
    "user,admin,expected",
    [
        (AUTHOR, False, True),
        (HR, True, True),
        (HR, False, False),
        (FINANCE, False, False),
        (RESPONDENT, False, False),
    ],
)
def test_who_may_read_individual_rows(user, admin, expected):
    assert bool(may_read_rows(user, AUTHOR_ID, admin)) is expected


def test_being_in_the_audience_does_not_let_you_read_the_rows():
    """The distinction the whole design rests on. An HR creator may answer an HR survey
    and may see its totals, and may not read what their colleagues individually said."""
    assert may_answer(HR, SurveyAudience.hr, OTHER_ID, admin=False)
    assert may_read_totals(HR, SurveyAudience.hr, OTHER_ID, admin=False)
    assert not may_read_rows(HR, OTHER_ID, admin=False)


@pytest.mark.parametrize(
    "user,audience,expected",
    [
        (HR, SurveyAudience.hr, True),
        (FINANCE, SurveyAudience.hr, False),
        (RESPONDENT, SurveyAudience.respondents, True),
        (RESPONDENT, SurveyAudience.hr, False),
    ],
)
def test_who_may_read_totals(user, audience, expected):
    assert bool(may_read_totals(user, audience, OTHER_ID, admin=False)) is expected


# ------------------------------------------------------------------------------- listing


def test_a_survey_you_cannot_answer_is_not_even_named_to_you():
    """Existence is information: 'Finance restructure feedback' says something before a
    single answer is given."""
    assert not may_list(HR, SurveyAudience.finance, OTHER_ID, admin=False)
    assert may_list(FINANCE, SurveyAudience.finance, OTHER_ID, admin=False)
    assert may_list(HR, SurveyAudience.finance, OTHER_ID, admin=True)


def test_an_author_always_sees_their_own_work():
    """Even aimed at a department they are not in, or with no audience at all, or they
    could create something and lose it."""
    assert may_list(AUTHOR, SurveyAudience.finance, AUTHOR_ID, admin=False)
    assert may_list(AUTHOR, None, AUTHOR_ID, admin=False)


# --------------------------------------------------------------------------------- admin


def test_admin_comes_from_the_allowlist_and_ignores_case():
    allowlist = frozenset({"Boss@Example.com"})
    assert is_admin(_user(UserRole.author, email="boss@example.com"), allowlist)
    assert not is_admin(_user(UserRole.author, email="someone@example.com"), allowlist)


def test_an_empty_allowlist_grants_nobody():
    assert not is_admin(AUTHOR, frozenset())


# ------------------------------------------------------------------- completeness


def test_every_department_audience_maps_to_a_department():
    """The failure this exists for is silent and fatal. `may_answer` looks the audience up
    in `_AUDIENCE_DEPARTMENT` with no fallback, so an audience added to the enum without a
    matching entry does not refuse anyone: it raises KeyError the first time somebody opens
    that survey. Enumerating the enum means the next department cannot be half-added.

    `respondents` is excluded deliberately. No department answers it, respondents do.
    """
    from app.access.rules import _AUDIENCE_DEPARTMENT

    departmental = {a for a in SurveyAudience if a is not SurveyAudience.respondents}
    assert departmental == set(
        _AUDIENCE_DEPARTMENT
    ), "every departmental audience needs an entry in _AUDIENCE_DEPARTMENT"


def test_every_department_can_be_aimed_at_except_admin():
    """Admin is grouping, not a team to survey, which is why the two enums are separate.
    Every other department should have an audience that reaches it."""
    aimable = {d.value for d in CreatorDepartment} - {"admin"}
    assert aimable <= {a.value for a in SurveyAudience}
