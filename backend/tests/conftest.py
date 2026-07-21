"""Test fixtures: a real Postgres test database with a fresh schema per test.

Uses the compose Postgres (a separate ``viewops_test`` database), so repository and
service logic is exercised against the real engine, not a stand-in.
"""

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db.base import Base
from app.runs import models as _runs  # noqa: F401  (register tables on metadata)
from app.templates import models as _templates  # noqa: F401
from app.users.models import User, UserRole

ADMIN_URL = "postgresql+asyncpg://viewops:viewops@localhost:5432/viewops"
TEST_URL = "postgresql+asyncpg://viewops:viewops@localhost:5432/viewops_test"


@pytest_asyncio.fixture
async def engine():
    admin = create_async_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        found = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = 'viewops_test'")
        )
        if not found:
            await conn.execute(text("CREATE DATABASE viewops_test"))
    await admin.dispose()

    eng = create_async_engine(TEST_URL)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    async with AsyncSession(engine, expire_on_commit=False) as sess:
        yield sess


@pytest_asyncio.fixture
async def author(session):
    user = User(email="author@test.dev", display_name="Test Author", role=UserRole.author)
    session.add(user)
    await session.flush()
    return user
