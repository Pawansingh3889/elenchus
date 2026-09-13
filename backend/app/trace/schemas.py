"""What the lens endpoints return: traced runs, spans, and totals across all runs.

Counts that were never reported stay distinguishable from zero. Token sums add only what
providers reported, and ``unmetered_attempts`` says how many attempts reported nothing,
so a total reads as "at least" whenever that count is not zero. A cost is None when no
attempt under it was priced.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TracedRun(BaseModel):
    """One run that has a trace, with what its turns cost and how long they took."""

    run_id: UUID
    survey_title: str
    started_at: datetime
    last_traced_at: datetime
    turns: int
    decisions: int
    retries: int
    attempts: int
    failed_attempts: int
    unmetered_attempts: int
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int
    reasoning_tokens: int
    cost_usd: float | None
    # Summed over turn spans: the wall time respondents waited, not the sum of attempts.
    turn_ms: int
    first_token_ms_p50: float | None


class SpanRead(BaseModel):
    """One span, flat. The page builds the tree from ``parent_id``."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_id: UUID | None
    run_id: UUID | None
    kind: str
    name: str
    started_at: datetime
    duration_ms: int
    error: str | None
    prompt_version: str | None
    tier: int | None
    model: str | None
    status: int | None
    prompt_tokens: int | None
    completion_tokens: int | None
    cached_tokens: int | None
    reasoning_tokens: int | None
    first_token_ms: int | None
    cost_usd: float | None
    attrs: dict[str, Any]


class TierStrip(BaseModel):
    """Every attempt one tier and model served, across all traced runs."""

    tier: int | None
    model: str | None
    attempts: int
    failed_attempts: int
    unmetered_attempts: int
    prompt_tokens: int
    completion_tokens: int
    cached_tokens: int
    reasoning_tokens: int
    cost_usd: float | None
    latency_ms_p50: float | None
    latency_ms_p95: float | None
    first_token_ms_p50: float | None
    first_token_ms_p95: float | None


class LensStrip(BaseModel):
    """The strip every lens page carries: totals across all traced runs, then per tier."""

    runs: int
    turns: int
    retries: int
    turn_ms_p50: float | None
    tiers: list[TierStrip]
