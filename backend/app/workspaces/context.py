"""Workspace attribution for operational records outside PostgreSQL."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import UUID

current_workspace: ContextVar[UUID | None] = ContextVar("current_workspace", default=None)


@contextmanager
def workspace_scope(workspace_id: UUID | None) -> Iterator[None]:
    token = current_workspace.set(workspace_id)
    try:
        yield
    finally:
        current_workspace.reset(token)
