"""pending_clarifications on survey_runs

Revision ID: e6f7a8b9c0d1
Revises: c4d1e8f07a26
Create Date: 2026-08-20 10:00:00.000000

The author-side follow-up: an author flags an out-of-context answer on a completed
run, and the engine appends one clarifying question to the run's transcript for the
respondent to answer if they return. This column is the pending state for that: the
question ids awaiting a reply, empty for every run that is not waiting on one.

The run's status stays ``completed`` the whole time. A clarification is not a re-run:
the conversation is finished, the dashboard counts it finished, and only this list
says "someone is owed one answer". It is JSONB rather than a join table because the
lifecycle is "append an id, clear on reply", and nothing ever queries by question id.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e6f7a8b9c0d1"
down_revision: str | Sequence[str] | None = "c4d1e8f07a26"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "survey_runs",
        sa.Column(
            "pending_clarifications",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("survey_runs", "pending_clarifications")
