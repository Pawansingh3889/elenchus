"""Idempotent dev seed: a few authors and respondents, plus the sample dataset.

Run with ``python -m app.seed``. Safe to run repeatedly (keyed on id).
"""

import asyncio
from uuid import UUID

from app.db.session import SessionFactory
from app.sample_data.loader import load_sample_data
from app.users.models import User, UserRole

SEED_USERS: list[tuple[UUID, str, str, UserRole]] = [
    (
        UUID("00000000-0000-0000-0000-0000000000a1"),
        "ava@viewops.dev",
        "Ava Author",
        UserRole.author,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000a2"),
        "arjun@viewops.dev",
        "Arjun Author",
        UserRole.author,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000b1"),
        "rosa@viewops.dev",
        "Rosa Respondent",
        UserRole.respondent,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000b2"),
        "ravi@viewops.dev",
        "Ravi Respondent",
        UserRole.respondent,
    ),
    (
        UUID("00000000-0000-0000-0000-0000000000b3"),
        "remy@viewops.dev",
        "Remy Respondent",
        UserRole.respondent,
    ),
]


async def seed() -> None:
    async with SessionFactory() as session:
        for uid, email, name, role in SEED_USERS:
            if await session.get(User, uid) is None:
                session.add(User(id=uid, email=email, display_name=name, role=role))
        await session.commit()
        surveys_added, runs_added = await load_sample_data(session)
    print(
        f"Seeded {len(SEED_USERS)} users; loaded {surveys_added} sample surveys "
        f"and {runs_added} runs (idempotent)."
    )


if __name__ == "__main__":
    asyncio.run(seed())
