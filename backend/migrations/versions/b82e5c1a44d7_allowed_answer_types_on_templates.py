"""allowed answer types on survey templates

Revision ID: b82e5c1a44d7
Revises: f1b6d38e05c4
Create Date: 2026-08-09 15:05:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b82e5c1a44d7'
down_revision: str | None = 'f1b6d38e05c4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # NOT NULL with an empty-list default. Empty is the whole vocabulary, not "unknown":
    # every survey drafted before this one existed was written with no restriction, so the
    # backfill states what was already true of them and no existing draft changes meaning.
    #
    # JSONB rather than an array of the answer_type enum. The set is authoring policy, not
    # a value any row is stored under, and keeping it out of the enum means adding an
    # answer type later is one enum change rather than two.
    op.add_column(
        "survey_templates",
        sa.Column(
            "allowed_answer_types",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("survey_templates", "allowed_answer_types")
