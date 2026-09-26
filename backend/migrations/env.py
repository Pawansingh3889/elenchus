"""Alembic environment (async).

Imports every domain's models so ``Base.metadata`` is complete for autogenerate,
and drives migrations through the async engine.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.embeddings import models as _embeddings_models  # noqa: F401
from app.evaluation import models as _evaluation_models  # noqa: F401
from app.interp import models as _interp_models  # noqa: F401
from app.prompts import models as _prompts_models  # noqa: F401
from app.runs import models as _runs_models  # noqa: F401
from app.templates import models as _templates_models  # noqa: F401
from app.trace import models as _trace_models  # noqa: F401
from app.users import models as _users_models  # noqa: F401
from app.workspaces import models as _workspace_models  # noqa: F401
from migrations.metadata import migration_metadata

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = migration_metadata()


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection: object) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)  # type: ignore[arg-type]
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as connection:
        await connection.run_sync(_do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
