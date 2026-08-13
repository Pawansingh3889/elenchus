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


# ------------------------------------------------------------------- identity


def test_the_seed_agrees_with_how_people_will_sign_in():
    """`role` is a stored column today and will be derived tomorrow.

    The intended rule is that whoever holds a Microsoft account is a creator and everyone
    else answers surveys and reaches the app by a link. Until real sign-in exists, `role`
    is the development shim standing in for that, and nothing stops the two disagreeing:
    an author with no Microsoft id would be somebody who may build surveys and cannot
    sign in, and a respondent with one would silently become an author the day the rule
    is switched on.

    So the seed is held to the rule now, while the data is small enough to fix.
    """
    from app.seed import SEED_USERS
    from app.users.models import UserRole

    for _, email, _, role, _, microsoft_id in SEED_USERS:
        has_id = microsoft_id is not None
        assert has_id is (role is UserRole.author), (
            f"{email} is {role.value} and {'has' if has_id else 'has no'} Microsoft id; "
            "role will be derived from that id, so the two must already agree"
        )


def test_no_two_people_share_a_microsoft_id():
    """It is an identity, and two accounts sharing one would be two people sharing it.
    Enforced by a unique constraint in the database; asserted here so a seed that broke
    it fails with a sentence rather than an IntegrityError at startup."""
    from app.seed import SEED_USERS

    ids = [m for *_, m in SEED_USERS if m is not None]
    assert len(ids) == len(set(ids))


def test_the_seed_only_decorates_its_own_users():
    """Every membership the seed grants must name a user the seed itself defines.

    The failure this pins happened: two ids were reused from a retired generation of
    SEED_USERS, still present in databases seeded before 10 Aug. The user insert
    silently skipped, the membership loop then attached the new group to whoever held
    the ids, and two bystanders quietly joined shift_managers. `seed()` now refuses an
    id whose email disagrees; this catches the same mistake before a database is
    involved at all.
    """
    from app.seed import SEED_GROUPS, SEED_USERS

    user_ids = [uid for uid, *_ in SEED_USERS]
    assert len(user_ids) == len(set(user_ids)), "two seed users share an id"
    unknown = {uid for uid, _ in SEED_GROUPS} - set(user_ids)
    assert not unknown, f"SEED_GROUPS decorates ids the seed does not define: {unknown}"
