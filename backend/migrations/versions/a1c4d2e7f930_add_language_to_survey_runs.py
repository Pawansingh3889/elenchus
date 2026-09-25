"""add language to survey runs

Revision ID: a1c4d2e7f930
Revises: bff33e6e35e1
Create Date: 2026-08-06 03:40:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "a1c4d2e7f930"
down_revision: str | None = "bff33e6e35e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # NOT NULL with a server default rather than nullable: every run is conducted in
    # some language, and "unknown" is not one of them. The default backfills existing
    # rows to English, which is what they were actually conducted in, so the column is
    # true of history rather than merely populated.
    op.add_column(
        "survey_runs",
        sa.Column("language", sa.String(length=8), nullable=False, server_default="en"),
    )


def downgrade() -> None:
    op.drop_column("survey_runs", "language")
