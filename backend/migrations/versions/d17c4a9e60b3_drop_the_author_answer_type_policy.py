"""drop the author-set answer type policy

Revision ID: d17c4a9e60b3
Revises: c93f6d2b18ae
Create Date: 2026-08-09 21:20:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'd17c4a9e60b3'
down_revision: str | None = 'c93f6d2b18ae'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Added earlier today and dropped the same day, deliberately rather than left in
    # place "in case". Authors do not choose answer types: free text is excluded while
    # the model drafts, which is a rule about drafting and lives in code, and a survey
    # that wants a text question gets one from the author by hand. A per-survey column
    # nothing writes is a field the next reader has to work out the meaning of.
    #
    # No data is lost that anyone chose: every row holds the empty list, because the
    # control shipped and was replaced before any author set one.
    op.drop_column("survey_templates", "allowed_answer_types")


def downgrade() -> None:
    op.add_column(
        "survey_templates",
        sa.Column(
            "allowed_answer_types",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )
