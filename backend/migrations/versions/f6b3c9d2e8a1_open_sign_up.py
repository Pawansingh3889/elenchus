"""Open sign-up: the signed_in audience and the sign-in log.

Revision ID: f6b3c9d2e8a1
Revises: e5a8b2c4d6f0

ADD VALUE runs inside Alembic's transaction, which Postgres has allowed since 12 as long
as the new value is not used in the same transaction, and nothing here uses it. It is
irreversible in place: Postgres cannot drop an enum value, so the downgrade leaves it.
"""

import sqlalchemy as sa
from alembic import op

revision = "f6b3c9d2e8a1"
down_revision = "e5a8b2c4d6f0"
branch_labels = None
depends_on = None

SCOPE = "nullif(current_setting('app.workspace_id', true), '')::uuid"


def upgrade() -> None:
    op.execute("ALTER TYPE survey_audience ADD VALUE IF NOT EXISTS 'signed_in' BEFORE 'person'")
    op.create_table(
        "sign_ins",
        sa.Column("workspace_id", sa.Uuid(), nullable=False, server_default=sa.text(SCOPE)),
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("provider", sa.String(16), nullable=False),
        sa.Column("created_account", sa.Boolean(), nullable=False),
        sa.Column(
            "signed_in_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    )
    op.create_index("ix_sign_ins_workspace_id", "sign_ins", ["workspace_id"])
    op.execute("ALTER TABLE sign_ins ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE sign_ins FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY workspace_rows ON sign_ins USING (workspace_id = {SCOPE}) "
        f"WITH CHECK (workspace_id = {SCOPE})"
    )


def downgrade() -> None:
    op.execute("DROP POLICY workspace_rows ON sign_ins")
    op.drop_index("ix_sign_ins_workspace_id", table_name="sign_ins")
    op.drop_table("sign_ins")
