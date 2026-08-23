"""merge app_settings and audience fixes

Revision ID: 0737cc8cd8b3
Revises: a1b2c3d4e5f6, f2b3c4d5e6f7
Create Date: 2026-08-23 01:51:30.824047

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '0737cc8cd8b3'
down_revision: str | None = ('a1b2c3d4e5f6', 'f2b3c4d5e6f7')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
