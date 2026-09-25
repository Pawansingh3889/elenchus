"""survey setting, written for the interviewer

Revision ID: c93f6d2b18ae
Revises: b82e5c1a44d7
Create Date: 2026-08-09 17:40:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "c93f6d2b18ae"
down_revision: str | None = "b82e5c1a44d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nullable, and no backfill. Unlike audience or the answer-type policy, there is no
    # value that is true of every survey written before this: NULL here means the author
    # has not described the workplace, which is a real state and the one they are all in.
    # An empty string would claim they had described it and said nothing.
    op.add_column("survey_templates", sa.Column("setting", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("survey_templates", "setting")
