"""drop app_settings table

Revision ID: 1cc867252136
Revises: a1b2c3d4e5f6
Create Date: 2026-08-22 09:31:39.493701

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '1cc867252136'
down_revision: str | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_table("app_settings")


def downgrade() -> None:
    pass
