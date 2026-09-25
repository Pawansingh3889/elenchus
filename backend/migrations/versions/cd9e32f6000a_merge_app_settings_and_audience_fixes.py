"""merge app_settings and audience fixes

Revision ID: cd9e32f6000a
Revises: a1b2c3d4e5f6, f2b3c4d5e6f7
Create Date: 2026-08-23 01:57:23.758000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "cd9e32f6000a"
down_revision: str | None = ("a1b2c3d4e5f6", "f2b3c4d5e6f7")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
