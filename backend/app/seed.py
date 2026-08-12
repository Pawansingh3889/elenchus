"""Idempotent dev seed: creators across every department, respondents, and the samples.

Run with ``python -m app.seed``. Safe to run repeatedly (keyed on id).

There is one creator per department rather than two unattached authors, because the
access rules are the interesting thing to look at now and they are invisible with a
single department: Ava in HR and Fatima in Finance seeing different lists is the whole
feature, and it cannot be demonstrated by a database that has only one team in it.

Nobody here is in IT, and so nobody here is an administrator. That is deliberate: IT
membership now grants admin, and a committed seed that shipped an administrator would
hand one to every checkout. Admin locally is still ADMIN_EMAILS, or moving one of these
accounts into IT yourself.

Everyone on the floor is in at least one group, including the senior people who hold
author accounts. That is the case worth being able to see: a survey aimed at supervisors
has to reach Ava, who signs in as a creator and is a supervisor on the line.
"""

import asyncio
from uuid import UUID

from app.db.session import SessionFactory
from app.sample_data.loader import load_sample_data
from app.users.models import CreatorDepartment, RespondentGroup, User, UserGroupMembership, UserRole

# The last field is a stand-in Entra object id. Authors have one because creators sign
# in with Microsoft; the floor has none and arrives by link instead. Nothing reads it
# yet, and test_seed_identity holds it consistent with `role`, so the day sign-in does
# read it the two already agree.
SEED_USERS: list[tuple[UUID, str, str, UserRole, CreatorDepartment | None, str | None]] = [
    (
        UUID("00000000-0000-0000-0000-0000000000a1"),
        "ava@elenchus.dev",
        "Ava Author",
        UserRole.author,
        # Management, matching the migration's remap of the old Operations department:
        # the walkthroughs and demo script all run as Ava, so she is the one whose
        # department has to be the ordinary case.
        CreatorDepartment.management,
        "entra-ava",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000a2"),
        "arjun@elenchus.dev",
        "Arjun Author",
        UserRole.author,
        CreatorDepartment.hr,
        "entra-arjun",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000a3"),
        "fatima@elenchus.dev",
        "Fatima Author",
        UserRole.author,
        CreatorDepartment.finance,
        "entra-fatima",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000a4"),
        "adaeze@elenchus.dev",
        "Adaeze Author",
        UserRole.author,
        # Management rather than IT, though this was the administration account before.
        # IT now grants admin, and a seeded administrator is a seeded way in: move this
        # account to IT yourself if that is what you want locally.
        CreatorDepartment.management,
        "entra-adaeze",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000a5"),
        "tomas@elenchus.dev",
        "Tomas Author",
        UserRole.author,
        CreatorDepartment.technical,
        "entra-tomas",
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000b1"),
        "rosa@elenchus.dev",
        "Rosa Respondent",
        UserRole.respondent,
        None,
        None,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000b2"),
        "ravi@elenchus.dev",
        "Ravi Respondent",
        UserRole.respondent,
        None,
        None,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000b3"),
        "remy@elenchus.dev",
        "Remy Respondent",
        UserRole.respondent,
        None,
        None,
    ),
]


# Who is on the floor, and as what. Ava is a supervisor as well as an author, which is
# the case the whole membership model exists for: her Teams login makes her a creator by
# `role`, and a survey aimed at supervisors is written for her all the same.
#
# Managers has members on purpose. The migration remaps every survey that used to name an
# office team onto `managers`, and landing those on an empty group would leave a shelf of
# surveys nobody can answer and a dashboard reporting a reach of zero for all of them.
SEED_GROUPS: list[tuple[UUID, tuple[RespondentGroup, ...]]] = [
    (UUID("00000000-0000-0000-0000-0000000000a1"), (RespondentGroup.supervisors,)),
    (UUID("00000000-0000-0000-0000-0000000000a2"), (RespondentGroup.managers,)),
    (UUID("00000000-0000-0000-0000-0000000000a4"), (RespondentGroup.managers,)),
    (UUID("00000000-0000-0000-0000-0000000000a5"), (RespondentGroup.qa,)),
    (UUID("00000000-0000-0000-0000-0000000000b1"), (RespondentGroup.operatives,)),
    # In two groups, because that is the thing a join table buys and a column could not:
    # a line leader who also covers QA is really in both.
    (
        UUID("00000000-0000-0000-0000-0000000000b2"),
        (RespondentGroup.line_leaders, RespondentGroup.qa),
    ),
    (UUID("00000000-0000-0000-0000-0000000000b3"), (RespondentGroup.operatives,)),
]


async def seed() -> None:
    async with SessionFactory() as session:
        for uid, email, name, role, department, microsoft_id in SEED_USERS:
            if await session.get(User, uid) is None:
                session.add(
                    User(
                        id=uid,
                        email=email,
                        display_name=name,
                        role=role,
                        department=department,
                        microsoft_id=microsoft_id,
                    )
                )
        await session.commit()
        memberships = 0
        for uid, groups in SEED_GROUPS:
            for group in groups:
                # Keyed on the pair, so re-running adds nothing and the seed stays safe to
                # run over a database somebody has already been using.
                if await session.get(UserGroupMembership, (uid, group)) is None:
                    session.add(UserGroupMembership(user_id=uid, group=group))
                    memberships += 1
        await session.commit()
        surveys_added, runs_added = await load_sample_data(session)
    print(
        f"Seeded {len(SEED_USERS)} users and {memberships} new group memberships; "
        f"loaded {surveys_added} sample surveys and {runs_added} runs (idempotent)."
    )


if __name__ == "__main__":
    asyncio.run(seed())
