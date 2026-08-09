"""Idempotent dev seed: creators across every department, respondents, and the samples.

Run with ``python -m app.seed``. Safe to run repeatedly (keyed on id).

There is one creator per department rather than two unattached authors, because the
access rules are the interesting thing to look at now and they are invisible with a
single department: Ava in HR and Fatima in Finance seeing different lists is the whole
feature, and it cannot be demonstrated by a database that has only one team in it.

Nobody here is an administrator. Admin comes from the ADMIN_EMAILS allowlist in the
environment, so putting a seeded address in it is how you grant yourself admin locally,
and a committed seed cannot hand it to anyone by accident.
"""

import asyncio
from uuid import UUID

from app.db.session import SessionFactory
from app.sample_data.loader import load_sample_data
from app.users.models import CreatorDepartment, User, UserRole

SEED_USERS: list[tuple[UUID, str, str, UserRole, CreatorDepartment | None]] = [
    (
        UUID("00000000-0000-0000-0000-0000000000a1"),
        "ava@elenchus.dev",
        "Ava Author",
        UserRole.author,
        # Operations, matching the migration's backfill: the walkthroughs and demo script
        # all run as Ava, so she is the one whose department has to be the ordinary case.
        CreatorDepartment.operations,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000a2"),
        "arjun@elenchus.dev",
        "Arjun Author",
        UserRole.author,
        CreatorDepartment.hr,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000a3"),
        "fatima@elenchus.dev",
        "Fatima Author",
        UserRole.author,
        CreatorDepartment.finance,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000a4"),
        "adaeze@elenchus.dev",
        "Adaeze Author",
        UserRole.author,
        # The admin *department*, which is grouping and not permission. This account has
        # no more rights than any other until its address is in ADMIN_EMAILS.
        CreatorDepartment.admin,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000b1"),
        "rosa@elenchus.dev",
        "Rosa Respondent",
        UserRole.respondent,
        None,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000b2"),
        "ravi@elenchus.dev",
        "Ravi Respondent",
        UserRole.respondent,
        None,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000b3"),
        "remy@elenchus.dev",
        "Remy Respondent",
        UserRole.respondent,
        None,
    ),
]


async def seed() -> None:
    async with SessionFactory() as session:
        for uid, email, name, role, department in SEED_USERS:
            if await session.get(User, uid) is None:
                session.add(
                    User(
                        id=uid,
                        email=email,
                        display_name=name,
                        role=role,
                        department=department,
                    )
                )
        await session.commit()
        surveys_added, runs_added = await load_sample_data(session)
    print(
        f"Seeded {len(SEED_USERS)} users; loaded {surveys_added} sample surveys "
        f"and {runs_added} runs (idempotent)."
    )


if __name__ == "__main__":
    asyncio.run(seed())
