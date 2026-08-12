"""The people directory: what an author is shown about who is where.

The page exists because reach was unreadable without it. A survey aimed at QA reporting
"1 of 2 answered" is correct and unexplainable when nothing on any screen says who the
two are, and one of them holds an author account because line leaders sign in with Teams.
"""

from uuid import uuid4

from app.users.models import CreatorDepartment, RespondentGroup, User, UserGroupMembership, UserRole
from app.users.schemas import PersonRead


def _user(**kw) -> User:
    # An explicit id: the column's `default=uuid4` is applied by SQLAlchemy at flush, and
    # nothing here touches a session. A real person always arrives from a row.
    return User(
        id=kw.pop("id", uuid4()),
        email=kw.pop("email", "someone@test.dev"),
        display_name=kw.pop("display_name", "Someone"),
        role=kw.pop("role", UserRole.respondent),
        **kw,
    )


def test_a_person_carries_their_department_and_groups():
    user = _user(
        display_name="Ava Author",
        role=UserRole.author,
        department=CreatorDepartment.management,
        memberships=[UserGroupMembership(group=RespondentGroup.supervisors)],
    )
    person = PersonRead.of(user)
    assert person.display_name == "Ava Author"
    assert person.department is CreatorDepartment.management
    assert person.groups == [RespondentGroup.supervisors]


def test_groups_come_back_in_a_stable_order():
    """`User.groups` is a set, and a set has no order. Without sorting, one person's
    badges could shuffle between refreshes, which reads as the data changing when
    nothing has."""
    both = [
        UserGroupMembership(group=RespondentGroup.qa),
        UserGroupMembership(group=RespondentGroup.line_leaders),
    ]
    first = PersonRead.of(_user(memberships=list(both)))
    second = PersonRead.of(_user(memberships=list(reversed(both))))
    assert first.groups == second.groups == [RespondentGroup.line_leaders, RespondentGroup.qa]


def test_somebody_in_no_group_is_shown_as_such():
    """A real state and worth seeing: an account in no group can answer nothing, not even
    a survey aimed at everyone, so an empty list here is the explanation for a person who
    is never asked anything."""
    person = PersonRead.of(_user(display_name="Fatima Author", role=UserRole.author))
    assert person.groups == []


def test_the_directory_does_not_carry_an_email():
    """The question this page answers is who the two people in an audience are, and a
    name, a department and a set of groups answer it. An address is contactable personal
    data that nothing on the page needs, so it is absent by construction rather than
    merely unrendered."""
    assert "email" not in PersonRead.model_fields
    person = PersonRead.of(_user(email="private@elenchus.dev"))
    assert "private@elenchus.dev" not in person.model_dump_json()
