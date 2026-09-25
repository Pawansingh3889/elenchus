"""Embedding vectors, cached by a hash of the text they describe.

The text itself is not stored here, only its SHA-256, the model and the vector. A vector
still carries meaning (embeddings can be partly inverted), so withdrawing a run deletes the
vectors of everything its respondent said, by hash, whichever model made them.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.workspaces.models import WorkspaceOwned


class EmbeddingVector(WorkspaceOwned, Base):
    __tablename__ = "embedding_vectors"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "digest", "model", name="uq_embedding_vectors_workspace_digest_model"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    digest: Mapped[str] = mapped_column(String(64), index=True)
    model: Mapped[str] = mapped_column(String(128))
    dimensions: Mapped[int] = mapped_column(Integer)
    vector: Mapped[list[float]] = mapped_column(ARRAY(Float))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(UTC)
    )
