"""Async engine, session factory, and the FastAPI session dependency."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.workspaces import repository as _workspace_context  # noqa: F401
from app.workspaces.context import workspace_scope

engine = create_async_engine(
    get_settings().database_url,
    pool_pre_ping=True,
    # See the pool fields in config.py: break-time is a burst of concurrent respondents,
    # each holding a connection across an LLM call, and the defaults queued half of them.
    pool_size=get_settings().db_pool_size,
    max_overflow=get_settings().db_pool_max_overflow,
)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped async session."""
    with workspace_scope(None):
        async with SessionFactory() as session:
            yield session
