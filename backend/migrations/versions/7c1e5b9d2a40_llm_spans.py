"""llm spans

Revision ID: 7c1e5b9d2a40
Revises: 1cc867252136
Create Date: 2026-09-13 09:00:00.000000

One row per turn, model decision, tier attempt and validation, linked by parent_id into
a tree per respondent message. See app/trace/models.py for why run_id and parent_id are
indexed but not foreign keys: spans are written while the turn still holds FOR UPDATE on
its run, and a foreign key check would wait on that lock forever.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7c1e5b9d2a40"
down_revision: str | None = "1cc867252136"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SPAN_KIND = sa.Enum("turn", "decision", "attempt", "validation", name="span_kind")


def upgrade() -> None:
    op.create_table(
        "llm_spans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("run_id", sa.Uuid(), nullable=True),
        sa.Column("kind", SPAN_KIND, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=True),
        sa.Column("tier", sa.SmallInteger(), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("status", sa.SmallInteger(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("cached_tokens", sa.Integer(), nullable=True),
        sa.Column("reasoning_tokens", sa.Integer(), nullable=True),
        sa.Column("first_token_ms", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(precision=14, scale=8), nullable=True),
        sa.Column(
            "attrs",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_llm_spans")),
    )
    op.create_index(op.f("ix_llm_spans_parent_id"), "llm_spans", ["parent_id"])
    op.create_index(op.f("ix_llm_spans_run_id"), "llm_spans", ["run_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_llm_spans_run_id"), table_name="llm_spans")
    op.drop_index(op.f("ix_llm_spans_parent_id"), table_name="llm_spans")
    op.drop_table("llm_spans")
    SPAN_KIND.drop(op.get_bind(), checkfirst=True)
