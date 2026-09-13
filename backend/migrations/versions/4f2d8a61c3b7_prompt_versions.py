"""prompt versions and activations

Revision ID: 4f2d8a61c3b7
Revises: 7c1e5b9d2a40
Create Date: 2026-09-13 12:00:00.000000

Conduct prompt versions saved from the admin screen, and the append-only log of which
version is live. The files under app/llm/prompts/ stay the seed versions; see
app/prompts/models.py for why neither table is ever updated.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4f2d8a61c3b7"
down_revision: str | None = "7c1e5b9d2a40"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prompt_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_prompt_versions_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prompt_versions")),
        sa.UniqueConstraint("name", name=op.f("uq_prompt_versions_name")),
    )
    op.create_index(op.f("ix_prompt_versions_family"), "prompt_versions", ["family"])
    op.create_table(
        "prompt_activations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("family", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("activated_by", sa.Uuid(), nullable=True),
        sa.Column(
            "activated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["activated_by"],
            ["users.id"],
            name=op.f("fk_prompt_activations_activated_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prompt_activations")),
    )
    op.create_index(op.f("ix_prompt_activations_family"), "prompt_activations", ["family"])


def downgrade() -> None:
    op.drop_index(op.f("ix_prompt_activations_family"), table_name="prompt_activations")
    op.drop_table("prompt_activations")
    op.drop_index(op.f("ix_prompt_versions_family"), table_name="prompt_versions")
    op.drop_table("prompt_versions")
