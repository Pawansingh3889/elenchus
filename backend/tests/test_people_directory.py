"""The people directory: what an author is shown about who is where.

The page exists because reach was unreadable without it. A survey aimed at QA reporting
"1 of 2 answered" is correct and unexplainable when nothing on any screen says who the
two are, and one of them authors surveys because the head of QA holds a manager band.
"""

from uuid import uuid4

from app.users.models import Band, Function, Hat, User, UserHat
from app.users.schemas import PersonRead


def _user(**kw) -> User:
    # An explicit id: the column's `default=uuid4` is applied by SQLAlchemy at flush, and
    # nothing here touches a session. A real person always arrives from a row.
    return User(
        id=kw.pop("id", uuid4()),
        email=kw.pop("email", "someone@test.dev"),
        display_name=kw.pop("display_name", "Someone"),
        **kw,
    )


def test_a_person_carries_their_job_and_hats():
    user = _user(
        display_name="Rohan Respondent",
        function=Function.production,
        band=Band.supervisor,
        hat_rows=[UserHat(hat=Hat.health_safety)],
    )
    person = PersonRead.of(user)
    assert person.display_name == "Rohan Respondent"
    assert person.function is Function.production
    assert person.band is Band.supervisor
    assert person.hats == [Hat.health_safety]


def test_the_directory_says_who_may_author():
    """Derived on the server, because band order is the server's fact: the page badges
    who can build surveys without the client re-inventing the manager cutoff."""
    shift_manager = PersonRead.of(_user(function=Function.production, band=Band.manager))
    operative = PersonRead.of(_user(function=Function.production, band=Band.operative))
    assert shift_manager.may_author is True
    assert operative.may_author is False


def test_an_authoring_band_without_a_sign_in_is_visible():
    """The badge case: somebody at manager band with no Entra id builds surveys today
    and cannot sign in the day the header shim is replaced. The page can only mark it
    if both facts arrive."""
    person = PersonRead.of(_user(function=Function.production, band=Band.manager))
    assert person.may_author is True
    assert person.has_microsoft_id is False


def test_somebody_with_no_job_is_shown_as_such():
    """A real state and worth seeing: an account with no job can answer nothing, not
    even a survey aimed at everyone, so an empty job here is the explanation for a
    person who is never asked anything."""
    person = PersonRead.of(_user(display_name="Service Account"))
    assert person.function is None
    assert person.band is None
    assert person.hats == []
    assert person.may_author is False


def test_the_directory_does_not_carry_an_email():
    """The question this page answers is who the two people in an audience are, and a
    name and a job answer it. An address is contactable personal data that nothing on
    the page needs, so it is absent by construction rather than merely unrendered."""
    assert "email" not in PersonRead.model_fields
    person = PersonRead.of(_user(email="private@elenchus.dev"))
    assert "private@elenchus.dev" not in person.model_dump_json()


# ------------------------------------------------------------------- identity


def test_the_seed_gives_sign_ins_to_the_authoring_bands():
    """The Entra id is a sign-in method now, nothing more, but the people who author
    still need one: they are who the app's authoring surface exists for, and an
    authoring band with no way to sign in is a locked door with a desk behind it.

    Rina is the one deliberate exception, kept so the directory's badge for exactly
    this state has a person to show it on. Naming her here means a second exception
    cannot slip in behind her.
    """
    from app.access import may_author
    from app.seed import SEED_USERS

    unexpected = []
    for _, email, name, function, band, microsoft_id in SEED_USERS:
        authoring = may_author(User(email=email, display_name=name, function=function, band=band))
        if authoring and microsoft_id is None and email != "rina@elenchus.dev":
            unexpected.append(email)
        if not authoring and microsoft_id is not None:
            unexpected.append(email)
    assert not unexpected, (
        f"seed users whose sign-in disagrees with their band: {unexpected}; "
        "authoring bands carry an Entra id (Rina excepted, deliberately), floor bands do not"
    )


def test_no_two_people_share_a_microsoft_id():
    """It is an identity, and two accounts sharing one would be two people sharing it.
    Enforced by a unique constraint in the database; asserted here so a seed that broke
    it fails with a sentence rather than an IntegrityError at startup."""
    from app.seed import SEED_USERS

    ids = [m for *_, m in SEED_USERS if m is not None]
    assert len(ids) == len(set(ids))


def test_the_seed_only_decorates_its_own_users():
    """Every hat the seed grants must name a user the seed itself defines.

    The failure this pins happened with the retired membership table: two ids were
    reused from an older generation of SEED_USERS, still present in databases seeded
    before 10 Aug. The user insert silently skipped, the decoration loop then attached
    rows to whoever held the ids, and two bystanders quietly gained a group. `seed()`
    refuses an id whose email disagrees; this catches the same mistake before a
    database is involved at all.
    """
    from app.seed import SEED_HATS, SEED_USERS

    user_ids = [uid for uid, *_ in SEED_USERS]
    assert len(user_ids) == len(set(user_ids)), "two seed users share an id"
    unknown = {uid for uid, _ in SEED_HATS} - set(user_ids)
    assert not unknown, f"SEED_HATS decorates ids the seed does not define: {unknown}"
