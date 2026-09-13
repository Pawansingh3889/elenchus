"""Trace spans: every turn, model decision, tier attempt and validation, linked as a tree.

The ledger file answers "what did calls cost"; this table answers "why": which decision
an attempt served, which refusal caused the retry that doubled a turn's cost, and how
long the engine spent on each. The pages that explain the model read it.

``run_id`` and ``parent_id`` are indexed but deliberately **not foreign keys**. Spans are
written in their own short transaction while the turn that produced them still holds
``FOR UPDATE`` on its run, and a foreign key check takes ``FOR KEY SHARE`` on the parent
row, which that lock blocks: the turn would wait on its own spans forever. Withdrawing a
run deletes its spans explicitly instead of by cascade.

No transcript is copied into a span. Attributes carry counts, tool names, question ids and
the engine's refusal reasons, and a refusal reason can quote the value a model proposed, so
withdrawing a run deletes its spans along with everything else it holds. The exact request
of each chat attempt, which does copy the transcript, is kept apart in ``llm_requests``
and deleted with the run in the same way.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.trace.enums import SpanKind

if TYPE_CHECKING:
    from app.llm.ledger import TraceSpan


class LLMSpan(Base):
    __tablename__ = "llm_spans"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    parent_id: Mapped[UUID | None] = mapped_column(index=True, default=None)
    run_id: Mapped[UUID | None] = mapped_column(index=True, default=None)
    kind: Mapped[SpanKind] = mapped_column(SAEnum(SpanKind, name="span_kind"))
    name: Mapped[str] = mapped_column(String(64))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text, default=None)
    prompt_version: Mapped[str | None] = mapped_column(String(64), default=None)
    # Attempt spans only: the same facts the ledger row carries, so a page can join a
    # tree to its costs without reading the file.
    tier: Mapped[int | None] = mapped_column(SmallInteger, default=None)
    model: Mapped[str | None] = mapped_column(String(128), default=None)
    status: Mapped[int | None] = mapped_column(SmallInteger, default=None)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, default=None)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, default=None)
    cached_tokens: Mapped[int | None] = mapped_column(Integer, default=None)
    reasoning_tokens: Mapped[int | None] = mapped_column(Integer, default=None)
    first_token_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(14, 8), default=None)
    attrs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    @classmethod
    def from_trace(cls, run_id: UUID | None, node: "TraceSpan") -> "LLMSpan":
        """The row for one span the ledger collected in memory."""
        return cls(
            id=node.id,
            parent_id=node.parent_id,
            run_id=run_id,
            kind=SpanKind(node.kind),
            name=node.name,
            started_at=node.started_at,
            duration_ms=node.duration_ms,
            error=node.error,
            prompt_version=node.prompt_version,
            tier=node.tier,
            model=node.model,
            status=node.status,
            prompt_tokens=node.prompt_tokens,
            completion_tokens=node.completion_tokens,
            cached_tokens=node.cached_tokens,
            reasoning_tokens=node.reasoning_tokens,
            first_token_ms=node.first_token_ms,
            # Through str, as add_llm_spend does, so a float's binary tail never reaches
            # the numeric column.
            cost_usd=None if node.cost_usd is None else Decimal(str(node.cost_usd)),
            attrs=node.attrs,
        )


class LLMRequest(Base):
    """The exact request of one traced chat attempt: the messages and tools it was sent.

    Kept so a local model can read precisely what the hosted one read. A prompt rebuilt
    later from the recorded state would be a different prompt, and an explanation of a
    different prompt explains nothing about the call that happened. Captured from
    13 Sep 2026 onward; attempts before that have no row.

    Keyed by the attempt span it belongs to, and like the span not a foreign key to the
    run, for the lock reason in this module's docstring. It holds what the respondent
    typed, so withdrawal deletes it explicitly.
    """

    __tablename__ = "llm_requests"

    span_id: Mapped[UUID] = mapped_column(primary_key=True)
    run_id: Mapped[UUID | None] = mapped_column(index=True, default=None)
    model: Mapped[str | None] = mapped_column(String(128), default=None)
    messages: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    tools: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    tool_choice: Mapped[Any] = mapped_column(JSONB, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    @classmethod
    def from_trace(cls, run_id: UUID | None, node: "TraceSpan") -> "LLMRequest | None":
        """The row for a span's captured request, or None when the span carries none."""
        if node.request is None:
            return None
        return cls(
            span_id=node.id,
            run_id=run_id,
            model=node.model,
            messages=node.request["messages"],
            tools=node.request.get("tools", []),
            tool_choice=node.request.get("tool_choice"),
            created_at=node.started_at,
        )
