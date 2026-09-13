"""llm requests

Revision ID: 6d1a4c8e2f93
Revises: 9b3e1d7a5c20
Create Date: 2026-09-13 18:00:00.000000

The exact messages and tools of each traced chat attempt, keyed by its span, so a local
model can read the prompt the hosted model read. Like llm_spans, run_id is indexed and not
a foreign key: a turn writes these while it holds FOR UPDATE on its run.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "6d1a4c8e2f93"
down_revision: str | None = "9b3e1d7a5c20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "llm_requests",
        sa.Column("span_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("messages", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tools", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tool_choice", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("span_id", name=op.f("pk_llm_requests")),
    )
    op.create_index(op.f("ix_llm_requests_run_id"), "llm_requests", ["run_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_llm_requests_run_id"), table_name="llm_requests")
    op.drop_table("llm_requests")
