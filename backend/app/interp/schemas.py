"""What the interpretability lens reads and returns.

The Analysis half mirrors interp/elenchus_interp/schemas.py, the service's contract. It is
repeated rather than shared because the service is its own project with its own
dependencies; a response that stops matching fails validation here, loudly.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class Section(BaseModel):
    key: str
    label: str
    kind: Literal["system", "tools", "message", "template"]
    role: str | None
    tokens: int


class ToolScore(BaseModel):
    name: str
    logprob: float
    probability: float


class LayerReading(BaseModel):
    layer: int
    norm: float
    tool_probabilities: dict[str, float]
    top_token: str


class LayerAttention(BaseModel):
    layer: int
    shares: dict[str, float]


class TokenWeight(BaseModel):
    position: int
    text: str
    section: str
    weight: float


class WordScore(BaseModel):
    text: str
    score: float


class SectionAttribution(BaseModel):
    positive: float
    negative: float


class Attribution(BaseModel):
    target: str
    sections: dict[str, SectionAttribution]
    tokens: list[TokenWeight]
    respondent_words: list[WordScore]


class ReadTimings(BaseModel):
    render_ms: int
    read_ms: int
    tools_ms: int
    total_ms: int


class Analysis(BaseModel):
    model: str
    revision: str
    device: str
    dtype: str
    prompt_tokens: int
    sections: list[Section]
    calls_a_tool: float
    tools: list[ToolScore]
    pick: str
    layers: list[LayerReading]
    attention: list[LayerAttention]
    attended_tokens: list[TokenWeight]
    timings: ReadTimings


class AttributionResult(BaseModel):
    model: str
    revision: str
    device: str
    prompt_tokens: int
    attribution: Attribution
    render_ms: int
    attribution_ms: int
    total_ms: int


class InterpStatus(BaseModel):
    enabled: bool
    reachable: bool
    model: str | None
    revision: str | None
    device: str | None
    # Why it is not reachable, in words, when it is not.
    detail: str | None


class CapturedAsk(BaseModel):
    """One captured call of the hosted model, and what Qwen made of it if it was read."""

    span_id: UUID
    run_id: UUID
    survey_title: str
    started_at: datetime
    hosted_model: str | None
    tools_offered: list[str]
    # What the hosted model called and whether the engine accepted it; None for an attempt
    # that failed before producing anything to check.
    hosted_pick: str | None
    outcome: str | None
    hosted_ms: int
    hosted_prompt_tokens: int | None
    hosted_cost_usd: float | None
    analysed: bool
    attributed: bool
    qwen_pick: str | None
    # How likely Qwen found the tool the hosted model actually called.
    qwen_probability_of_hosted_pick: float | None
    agrees: bool | None
    analysis_ms: int | None
    analysis_cost_usd: float | None
    attribution_ms: int | None
    attribution_cost_usd: float | None


class StoredAttribution(BaseModel):
    attributed_at: datetime
    duration_ms: int
    cost_usd: float | None
    result: AttributionResult


class StoredAnalysis(BaseModel):
    span_id: UUID
    run_id: UUID | None
    target_tool: str | None
    analysed_at: datetime
    duration_ms: int
    cost_usd: float | None
    hosted_model: str | None
    hosted_ms: int
    hosted_cost_usd: float | None
    analysis: Analysis
    # Run separately, because it takes several times as long as the reading.
    attribution: StoredAttribution | None
