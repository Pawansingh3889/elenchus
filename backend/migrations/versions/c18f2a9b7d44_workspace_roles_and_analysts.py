"""Workspace roles and survey-scoped analyst access.

Revision ID: c18f2a9b7d44
Revises: ab47d902e631
"""

import sqlalchemy as sa
from alembic import op

revision = "c18f2a9b7d44"
down_revision = "ab47d902e631"
branch_labels = None
depends_on = None

SCOPE = "nullif(current_setting('app.workspace_id', true), '')::uuid"
TABLES = ("survey_analysts", "survey_access_changes")


def upgrade() -> None:
    role = sa.Enum("owner", "admin", "author", "analyst", "respondent", name="workspace_role")
    role.create(op.get_bind(), checkfirst=True)
    op.add_column("users", sa.Column("workspace_role", role, nullable=True))

    op.create_table(
        "survey_analysts",
        sa.Column("workspace_id", sa.Uuid(), nullable=False, server_default=sa.text(SCOPE)),
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("analyst_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_by", sa.Uuid(), nullable=False),
        sa.Column(
            "assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("template_id", "analyst_id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["survey_templates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analyst_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"]),
    )
    op.create_index("ix_survey_analysts_workspace_id", "survey_analysts", ["workspace_id"])
    op.create_table(
        "survey_access_changes",
        sa.Column("workspace_id", sa.Uuid(), nullable=False, server_default=sa.text(SCOPE)),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("analyst_id", sa.Uuid(), nullable=False),
        sa.Column("changed_by", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column(
            "changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["survey_templates.id"]),
        sa.ForeignKeyConstraint(["analyst_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_survey_access_changes_workspace_id", "survey_access_changes", ["workspace_id"]
    )

    for table, column, parent in (
        ("survey_analysts", "template_id", "survey_templates"),
        ("survey_analysts", "analyst_id", "users"),
        ("survey_analysts", "assigned_by", "users"),
        ("survey_access_changes", "template_id", "survey_templates"),
        ("survey_access_changes", "analyst_id", "users"),
        ("survey_access_changes", "changed_by", "users"),
    ):
        ondelete = (
            "SET NULL" if table == "survey_access_changes" and column == "changed_by" else None
        )
        op.create_foreign_key(
            f"fk_{table}_{column}_workspace",
            table,
            parent,
            ["workspace_id", column],
            ["workspace_id", "id"],
            ondelete=ondelete,
            deferrable=True,
            initially="DEFERRED",
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
    for table, column, _parent in (
        ("survey_access_changes", "changed_by", "users"),
        ("survey_access_changes", "analyst_id", "users"),
        ("survey_access_changes", "template_id", "survey_templates"),
        ("survey_analysts", "assigned_by", "users"),
        ("survey_analysts", "analyst_id", "users"),
        ("survey_analysts", "template_id", "survey_templates"),
    ):
        op.drop_constraint(f"fk_{table}_{column}_workspace", table, type_="foreignkey")
    op.drop_index("ix_survey_access_changes_workspace_id", table_name="survey_access_changes")
    op.drop_table("survey_access_changes")
    op.drop_index("ix_survey_analysts_workspace_id", table_name="survey_analysts")
    op.drop_table("survey_analysts")
    op.drop_column("users", "workspace_role")
    sa.Enum(name="workspace_role").drop(op.get_bind(), checkfirst=True)
