"""Add owner-configured response retention and non-identifying purge records.

Revision ID: d4e7f9a1b2c3
Revises: c18f2a9b7d44
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "d4e7f9a1b2c3"
down_revision = "c18f2a9b7d44"
branch_labels = None
depends_on = None

SCOPE = "nullif(current_setting('app.workspace_id', true), '')::uuid"
TABLES = (
    "workspace_retention_changes",
    "response_usage_totals",
    "response_deletion_audits",
)


def upgrade() -> None:
    op.add_column(
        "workspaces",
        sa.Column(
            "response_retention_days", sa.Integer(), nullable=False, server_default=sa.text("90")
        ),
    )
    op.create_table(
        "workspace_retention_changes",
        sa.Column("workspace_id", sa.Uuid(), nullable=False, server_default=sa.text(SCOPE)),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("changed_by", sa.Uuid(), nullable=True),
        sa.Column("before_days", sa.Integer(), nullable=False),
        sa.Column("after_days", sa.Integer(), nullable=False),
        sa.Column(
            "changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    )
    op.create_index(
        "ix_workspace_retention_changes_workspace_id",
        "workspace_retention_changes",
        ["workspace_id"],
    )
    op.create_table(
        "response_usage_totals",
        sa.Column("workspace_id", sa.Uuid(), nullable=False, server_default=sa.text(SCOPE)),
        sa.Column("month_start", sa.Date(), nullable=False),
        sa.Column("completed_responses", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("deleted_runs", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("llm_calls", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("llm_prompt_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "llm_completion_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("llm_unmetered_calls", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("llm_cost_usd", sa.Numeric(18, 8), nullable=False, server_default=sa.text("0")),
        sa.PrimaryKeyConstraint("workspace_id", "month_start"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    )
    op.create_table(
        "response_deletion_audits",
        sa.Column("workspace_id", sa.Uuid(), nullable=False, server_default=sa.text(SCOPE)),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("triggered_by", sa.Uuid(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "deleted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("usage", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    )
    op.create_index(
        "ix_response_deletion_audits_workspace_id",
        "response_deletion_audits",
        ["workspace_id"],
    )
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY workspace_rows ON {table} USING (workspace_id = {SCOPE}) "
            f"WITH CHECK (workspace_id = {SCOPE})"
        )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.execute(f"DROP POLICY workspace_rows ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_response_deletion_audits_workspace_id", table_name="response_deletion_audits")
    op.drop_table("response_deletion_audits")
    op.drop_table("response_usage_totals")
    op.drop_index(
        "ix_workspace_retention_changes_workspace_id", table_name="workspace_retention_changes"
    )
    op.drop_table("workspace_retention_changes")
    op.drop_column("workspaces", "response_retention_days")
