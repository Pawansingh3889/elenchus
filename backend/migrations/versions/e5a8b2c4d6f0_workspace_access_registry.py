"""Add invitation and approved employee-roster records.

Revision ID: e5a8b2c4d6f0
Revises: d4e7f9a1b2c3
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "e5a8b2c4d6f0"
down_revision = "d4e7f9a1b2c3"
branch_labels = None
depends_on = None

SCOPE = "nullif(current_setting('app.workspace_id', true), '')::uuid"
TABLES = ("workspace_invitations", "employee_roster", "workspace_access_changes")


def upgrade() -> None:
    op.create_table(
        "workspace_invitations",
        sa.Column("workspace_id", sa.Uuid(), nullable=False, server_default=sa.text(SCOPE)),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("workspace_role", sa.String(16), nullable=False),
        sa.Column("function", sa.String(32), nullable=False),
        sa.Column("band", sa.String(32), nullable=False),
        sa.Column("token_digest", sa.String(64), nullable=False, unique=True),
        sa.Column("invited_by", sa.Uuid(), nullable=False),
        sa.Column(
            "invited_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    )
    op.create_index(
        "ix_workspace_invitations_workspace_id", "workspace_invitations", ["workspace_id"]
    )
    op.create_table(
        "employee_roster",
        sa.Column("workspace_id", sa.Uuid(), nullable=False, server_default=sa.text(SCOPE)),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("function", sa.String(32), nullable=False),
        sa.Column("band", sa.String(32), nullable=False),
        sa.Column("approved_by", sa.Uuid(), nullable=False),
        sa.Column(
            "approved_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    )
    op.create_index("ix_employee_roster_workspace_id", "employee_roster", ["workspace_id"])
    op.create_table(
        "workspace_access_changes",
        sa.Column("workspace_id", sa.Uuid(), nullable=False, server_default=sa.text(SCOPE)),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("access_kind", sa.String(16), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("changed_by", sa.Uuid(), nullable=True),
        sa.Column(
            "changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("details", postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    )
    op.create_index(
        "ix_workspace_access_changes_workspace_id", "workspace_access_changes", ["workspace_id"]
    )
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY workspace_rows ON {table} USING (workspace_id = {SCOPE}) "
            f"WITH CHECK (workspace_id = {SCOPE})"
        )
        op.execute(
            f"CREATE POLICY verified_email_lookup ON {table} FOR SELECT USING ("
            "email = nullif(current_setting('app.verified_email', true), ''))"
        )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.execute(f"DROP POLICY verified_email_lookup ON {table}")
        op.execute(f"DROP POLICY workspace_rows ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_workspace_access_changes_workspace_id", table_name="workspace_access_changes")
    op.drop_table("workspace_access_changes")
    op.drop_index("ix_employee_roster_workspace_id", table_name="employee_roster")
    op.drop_table("employee_roster")
    op.drop_index("ix_workspace_invitations_workspace_id", table_name="workspace_invitations")
    op.drop_table("workspace_invitations")
