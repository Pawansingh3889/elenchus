from pydantic import BaseModel


class LlmModelStats(BaseModel):
    model: str
    tier: int | None = None
    calls: int
    total_prompt_tokens: int
    total_completion_tokens: int
    avg_latency_ms: float
    error_count: int


class LlmRunSummary(BaseModel):
    run_id: str | None = None
    model: str
    tier: int | None = None
    calls: int
    prompt_tokens: int
    completion_tokens: int
    avg_latency_ms: float
    error_count: int
    first_ts: str
    last_ts: str
    ops: list[str] = []


class LlmEntry(BaseModel):
    ts: str
    op: str | None = None
    tier: int | None = None
    model: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: int | None = None
    status: int | None = None
    error: str | None = None
    cost_usd: float | None = None


class LlmReport(BaseModel):
    total_entries: int
    total_runs: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost_usd: float
    avg_latency_ms: float
    models: list[LlmModelStats]
    runs: list[LlmRunSummary]


class LlmDailySpend(BaseModel):
    day: str
    tier: int | None = None
    model: str | None = None
    calls: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: int = 0
    error_count: int = 0


class LlmSpendSummary(BaseModel):
    days: list[LlmDailySpend]
    total_cost_usd: float
    total_calls: int
    total_errors: int
