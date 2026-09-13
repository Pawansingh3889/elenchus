"""One stored analysis per captured attempt: what Qwen3-0.6B read in its prompt.

Keyed by the attempt span, and like spans and requests the run is indexed without a
foreign key, for the lock reason in app/trace/models.py. The result quotes the tokens of
what the respondent typed, so withdrawing a run deletes it explicitly.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InterpAnalysis(Base):
    __tablename__ = "interp_analyses"

    span_id: Mapped[UUID] = mapped_column(primary_key=True)
    run_id: Mapped[UUID | None] = mapped_column(index=True, default=None)
    model: Mapped[str] = mapped_column(String(128))
    revision: Mapped[str] = mapped_column(String(64))
    device: Mapped[str] = mapped_column(String(32))
    # The tool the hosted model called, which the attribution explains; None when the
    # attempt produced no call the engine could check.
    target_tool: Mapped[str | None] = mapped_column(String(64), default=None)
    result: Mapped[dict[str, Any]] = mapped_column(JSONB)
    # Measured by the backend around the whole request, so it includes the network and
    # any wait behind another analysis; the result's own timings are the model's part.
    duration_ms: Mapped[int] = mapped_column(Integer)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(14, 8), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Gradient attribution toward target_tool, asked for separately because it takes several
    # times as long as the reading; measured and priced the same way.
    attribution: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    attribution_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    attribution_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(14, 8), default=None)
    attributed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
