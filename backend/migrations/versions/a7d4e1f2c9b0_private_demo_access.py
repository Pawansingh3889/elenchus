"""Private demo passes, persistent usage and pre-call spending reservations.

Revision ID: a7d4e1f2c9b0
Revises: f6b3c9d2e8a1
"""

import sqlalchemy as sa
from alembic import op

revision = "a7d4e1f2c9b0"
down_revision = "f6b3c9d2e8a1"
branch_labels = None
depends_on = None
SCOPE = "nullif(current_setting('app.workspace_id', true), '')::uuid"


def _owned(name: str, *columns: sa.Column, constraints: tuple = ()) -> None:
    op.create_table(
        name,
        sa.Column("workspace_id", sa.Uuid(), nullable=False, server_default=sa.text(SCOPE)),
        sa.Column("id", sa.Uuid(), primary_key=True),
        *columns,
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        *constraints,
    )
    op.create_index(f"ix_{name}_workspace_id", name, ["workspace_id"])
    op.execute(f"ALTER TABLE {name} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {name} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY workspace_rows ON {name} USING (workspace_id = {SCOPE}) WITH CHECK (workspace_id = {SCOPE})"
    )


def upgrade() -> None:
    op.add_column("users", sa.Column("demo_survey_id", sa.Uuid(), nullable=True))
    op.add_column(
        "survey_templates",
        sa.Column("sessions_started", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute(
        "UPDATE survey_templates SET sessions_started = (SELECT count(*) FROM survey_runs WHERE template_id = survey_templates.id)"
    )
    _owned(
        "demo_access",
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("pass_digest", sa.String(64), nullable=False),
        sa.Column(
            "issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("surveys_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("customer_product", sa.String(200)),
        sa.Column("customer_until", sa.DateTime(timezone=True)),
        sa.Column("monthly_response_allowance", sa.Integer()),
        sa.Column("approved_by", sa.String(320)),
        constraints=(
            sa.UniqueConstraint("workspace_id"),
            sa.ForeignKeyConstraint(
                ["workspace_id", "owner_id"],
                ["users.workspace_id", "users.id"],
                name="fk_demo_access_owner_id_workspace",
                deferrable=True,
                initially="DEFERRED",
            ),
        ),
    )
    _owned(
        "demo_registry",
        sa.Column("company", sa.String(200), nullable=False),
        sa.Column("contact_email", sa.String(320), nullable=False),
        sa.Column("issued_by", sa.String(320), nullable=False),
        sa.Column(
            "issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    _owned(
        "demo_usage",
        sa.Column("month_start", sa.Date(), nullable=False),
        sa.Column("sessions_started", sa.Integer(), nullable=False, server_default="0"),
        constraints=(sa.UniqueConstraint("workspace_id", "month_start"),),
    )
    _owned(
        "demo_spend",
        sa.Column("demo_workspace_id", sa.Uuid(), nullable=False),
        sa.Column("month_start", sa.Date(), nullable=False),
        sa.Column("model", sa.String(200), nullable=False),
        sa.Column("reserved_usd", sa.Numeric(18, 8), nullable=False),
        sa.Column("actual_usd", sa.Numeric(18, 8)),
        sa.Column("failed", sa.Boolean()),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_demo_spend_month_start", "demo_spend", ["month_start"])


def downgrade() -> None:
    for name in ("demo_spend", "demo_usage", "demo_registry", "demo_access"):
        op.drop_table(name)
    op.drop_column("survey_templates", "sessions_started")
    op.drop_column("users", "demo_survey_id")
