"""Placeholder migration to resolve Railway migration state mismatch

This migration was created to match the Railway database state where revision
1cc867252136 was expected but didn't exist in the codebase. It serves as a
bridge to allow the application to start.

Revision ID: 1cc867252136
Revises: cd9e32f6000a
Create Date: 2026-08-24 09:37:32.983046

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "1cc867252136"
down_revision: str | None = "cd9e32f6000a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Empty migration - this only exists to match Railway's expected state
    pass


def downgrade() -> None:
    pass
