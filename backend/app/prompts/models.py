"""Prompt versions written from the browser, and the log of which one is live.

Prompts are still versioned, and a stored ``prompt_version`` still resolves to exactly one
text. What changed on 13 Sep 2026 is where a version can live: the files under
``app/llm/prompts/`` remain the seed versions the code names, and an administrator can add
later versions here without a deploy.

Both tables are append-only. A saved version is never edited, because every turn, ledger row
and span recorded against its name would silently start describing different text. An
activation is never updated either: which version was live, when, and who switched it is
the history an unexplained change in cost or behaviour is traced back through.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # The family is the name without its version: "conduct" for "conduct_v9".
    family: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    body: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text, default=None)
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(UTC)
    )


class PromptActivation(Base):
    __tablename__ = "prompt_activations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    family: Mapped[str] = mapped_column(String(64), index=True)
    # A file version or a database version; resolved by name, so not a foreign key.
    name: Mapped[str] = mapped_column(String(64))
    activated_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    # Client-side so two activations in one transaction still order.
    activated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(UTC)
    )
