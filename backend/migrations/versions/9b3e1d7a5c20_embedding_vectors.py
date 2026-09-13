"""embedding vectors

Revision ID: 9b3e1d7a5c20
Revises: 4f2d8a61c3b7
Create Date: 2026-09-13 15:00:00.000000

A float array per text, keyed by the text's SHA-256 and the model, with no text stored.
Not pgvector: the image does not ship it and the data is hundreds of rows, where cosine in
Python is milliseconds. Revisit past tens of thousands of rows.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "9b3e1d7a5c20"
down_revision: str | None = "4f2d8a61c3b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "embedding_vectors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("digest", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("vector", postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_embedding_vectors")),
        sa.UniqueConstraint("digest", "model", name="uq_embedding_vectors_digest_model"),
    )
    op.create_index(op.f("ix_embedding_vectors_digest"), "embedding_vectors", ["digest"])


def downgrade() -> None:
    op.drop_index(op.f("ix_embedding_vectors_digest"), table_name="embedding_vectors")
    op.drop_table("embedding_vectors")
