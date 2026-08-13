"""account change log

Revision ID: f3a9c15d2b78
Revises: e8b3f60c9d47
Create Date: 2026-08-13 12:20:00.000000

The record that makes a moving reach number explainable. Reach is live by decision:
who a survey is for is whoever is in the group today, so every denominator moves when
membership does. That was chosen over freezing membership into published versions, and
this table is the half of the deal that makes it honest: when a completion rate drops
overnight, the answer to "why" is a row here saying who was moved out of which group,
when, and by whom.

Append-only. Nothing updates or deletes these rows; the service only ever inserts.
There is deliberately no ORM relationship pointing at it either, so no code path can
load a person "with their history" by accident.

Both people columns survive account deletion as SET NULL rather than taking the log
row with them: an audit trail that vanishes with its subject is not one.

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f3a9c15d2b78"
down_revision: str | None = "e8b3f60c9d47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "account_changes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("changed_by", sa.Uuid(), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # {kind: created|updated, before: {...}|null, after: {...}}, where the snapshots
        # carry exactly the fields an administrator controls. JSONB rather than columns
        # because the shape is a record of what the form said, not a table to query by
        # field; the queries this table answers are all "what happened to this person".
        sa.Column("change", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    # The one read path: this person's history, newest first.
    op.create_index(
        "ix_account_changes_user_changed_at",
        "account_changes",
        ["user_id", "changed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_account_changes_user_changed_at", table_name="account_changes")
    op.drop_table("account_changes")
