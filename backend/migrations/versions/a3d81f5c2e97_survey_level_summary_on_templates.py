"""survey level summary on templates

Revision ID: a3d81f5c2e97
Revises: f9c2a71b6e04
Create Date: 2026-08-11 00:20:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a3d81f5c2e97'
down_revision: str | None = 'f9c2a71b6e04'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nullable, and NULL means "nobody has asked for one yet", which is true of every
    # survey that exists today and stays true of any survey whose author never presses
    # the button. Generating one costs model calls, so it is author-triggered like the
    # per-run summary and the column is the cache rather than a field to be filled.
    #
    # Unlike the per-run summary, what this describes is not immutable: a completed run
    # never changes, a survey's set of responses does. So the stored document carries the
    # version and the run count it was made from, and the service regenerates when either
    # has moved. A cached aggregate served after the numbers changed is not stale, it is
    # wrong, and there is no way to tell from the prose.
    op.add_column(
        "survey_templates",
        sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("survey_templates", "summary")
