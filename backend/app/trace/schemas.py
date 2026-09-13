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
    template_id: UUID
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


class AttemptRow(BaseModel):
    """One call to one tier, placed in its run and turn. The Inference page's unit."""

    id: UUID
    run_id: UUID
    survey_title: str
    started_at: datetime
    # 1-based, in the order the run's turns happened.
    turn_number: int
    question_index: int | None
    # Whether the ask this attempt served was a nudged retry after a refusal.
    retry: bool
    transcript_messages: int | None
    tier: int | None
    model: str | None
    status: int | None
    error: str | None
    duration_ms: int
    first_token_ms: int | None
    prompt_tokens: int | None
    cached_tokens: int | None
    completion_tokens: int | None
    reasoning_tokens: int | None
    cost_usd: float | None


class DecisionRow(BaseModel):
    """One ask of the model, with what the engine knew, what it offered, what the model
    picked, what the check concluded, and what the ask's own calls cost.

    State fields are None on decisions traced before they were recorded (13 Sep 2026),
    which is unknown, not false.
    """

    id: UUID
    run_id: UUID
    survey_title: str
    started_at: datetime
    turn_number: int
    question_index: int | None
    retry: bool
    duration_ms: int
    error: str | None
    answer_type: str | None
    follow_up_policy: str | None
    forced_probe: bool | None
    probe_outstanding: bool | None
    scripted_recorded: bool | None
    recorded_this_turn: bool | None
    follow_ups_used: int | None
    replies_used: int | None
    transcript_messages: int | None
    tools_offered: list[str]
    resolved_to: str | None
    # From the ask's own validation span. None when the model never produced an action
    # to check (the call failed, or it chatted and was nudged).
    picked: str | None
    outcome: str | None
    reason: str | None
    # The attempts directly under this ask, not under a retry nested beneath it, so a
    # refusal's cost and its retry's cost stay apart.
    attempts: int
    failed_attempts: int
    attempt_ms: int
    cost_usd: float | None
