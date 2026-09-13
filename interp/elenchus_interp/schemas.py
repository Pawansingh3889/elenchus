"""The contract with the backend: what is asked, and what comes back."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalyseRequest(BaseModel):
    # The captured request exactly as the hosted model received it, in OpenAI's shape.
    messages: list[dict[str, Any]] = Field(min_length=1)
    tools: list[dict[str, Any]] = Field(min_length=1)


class AttributeRequest(AnalyseRequest):
    # The tool the hosted model actually called: the choice the attribution explains.
    target_tool: str


class Section(BaseModel):
    """A part of the prompt, and how many of its tokens the model read."""

    key: str
    label: str
    kind: Literal["system", "tools", "message", "template"]
    role: str | None
    tokens: int


class ToolScore(BaseModel):
    name: str
    # Log-probability of writing this tool's name at the call, summed over its tokens.
    logprob: float
    # The same, normalised over the tools that were offered.
    probability: float


class LayerReading(BaseModel):
    """The logit lens at the moment the tool name is about to be written."""

    layer: int
    norm: float
    tool_probabilities: dict[str, float]
    top_token: str


class LayerAttention(BaseModel):
    """Where that moment's attention went, averaged over heads, as a share per section."""

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
    # Shares of the total absolute attribution, so positive plus negative over every
    # section adds to one.
    positive: float
    negative: float


class Attribution(BaseModel):
    """Gradient times input: how much each prompt token moved the chosen tool's probability."""

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
    # Probability that the first thing written is a tool call at all.
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


class Health(BaseModel):
    model: str
    revision: str
    device: str
    ready: bool
