"""app_settings table for runtime LLM tier overrides

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-08-21 17:45:00.000000

A singleton row that stores per-tier runtime overrides as JSONB. An administrator
can change timeout_seconds, prompt_cache, max_completion_tokens, and enabled
flags without restarting the process. Fields absent from the stored dict fall back
to the environment-bound Settings values.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.String(32), primary_key=True, default="singleton"),
        sa.Column("tier_config", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_app_settings_singleton",
        "app_settings",
        "(id = 'singleton')",
    )


def downgrade() -> None:
    op.drop_table("app_settings")
