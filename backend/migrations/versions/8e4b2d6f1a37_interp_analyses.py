"""interp analyses

Revision ID: 8e4b2d6f1a37
Revises: 6d1a4c8e2f93
Create Date: 2026-09-13 19:00:00.000000

One stored reading per captured attempt, from the local interpretability model. Like the
spans and requests it reads, run_id is indexed and not a foreign key.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8e4b2d6f1a37"
down_revision: str | None = "6d1a4c8e2f93"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interp_analyses",
        sa.Column("span_id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("revision", sa.String(length=64), nullable=False),
        sa.Column("device", sa.String(length=32), nullable=False),
        sa.Column("target_tool", sa.String(length=64), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(precision=14, scale=8), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attribution", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("attribution_ms", sa.Integer(), nullable=True),
        sa.Column("attribution_cost_usd", sa.Numeric(precision=14, scale=8), nullable=True),
        sa.Column("attributed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("span_id", name=op.f("pk_interp_analyses")),
    )
    op.create_index(op.f("ix_interp_analyses_run_id"), "interp_analyses", ["run_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_interp_analyses_run_id"), table_name="interp_analyses")
    op.drop_table("interp_analyses")
