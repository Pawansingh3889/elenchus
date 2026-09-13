"""eval runs

Revision ID: 5f1c7d9e2a48
Revises: 3c8e5a1f9b62
Create Date: 2026-09-13 21:00:00.000000

One row per scripted scenario run in an evaluation batch: what it was pinned to, where it
got to, its checks, and what it cost under the batch's cap.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "5f1c7d9e2a48"
down_revision: str | None = "3c8e5a1f9b62"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EVAL_RUN_STATUS = postgresql.ENUM(
    "queued", "running", "completed", "capped", "failed", name="eval_run_status", create_type=False
)


def upgrade() -> None:
    EVAL_RUN_STATUS.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "eval_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("scenario", sa.String(length=32), nullable=False),
        sa.Column("tier", sa.SmallInteger(), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("status", EVAL_RUN_STATUS, nullable=False),
        sa.Column("cap_usd", sa.Numeric(precision=14, scale=8), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("template_id", sa.Uuid(), nullable=True),
        sa.Column("turns", sa.Integer(), nullable=False),
        sa.Column("answers", sa.Integer(), nullable=False),
        sa.Column("hard_failures", sa.Integer(), nullable=False),
        sa.Column("soft_failures", sa.Integer(), nullable=False),
        sa.Column("checks", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cost_usd", sa.Numeric(precision=14, scale=8), nullable=False),
        sa.Column("unmetered_calls", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["survey_runs.id"],
            name=op.f("fk_eval_runs_run_id_survey_runs"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_eval_runs_created_by_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_eval_runs")),
    )
    op.create_index(op.f("ix_eval_runs_batch_id"), "eval_runs", ["batch_id"])
    op.create_index(op.f("ix_eval_runs_run_id"), "eval_runs", ["run_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_eval_runs_run_id"), table_name="eval_runs")
    op.drop_index(op.f("ix_eval_runs_batch_id"), table_name="eval_runs")
    op.drop_table("eval_runs")
    EVAL_RUN_STATUS.drop(op.get_bind(), checkfirst=True)
