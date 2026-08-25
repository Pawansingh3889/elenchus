from pydantic import BaseModel


class LlmModelStats(BaseModel):
    model: str
    tier: int | None = None
    calls: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_context_tokens: int
    avg_latency_ms: float
    error_count: int


class LlmRunSummary(BaseModel):
    run_id: str | None = None
    model: str
    tier: int | None = None
    calls: int
    prompt_tokens: int
    completion_tokens: int
    context_tokens: int
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
    context_tokens: int | None = None
    latency_ms: int | None = None
    status: int | None = None
    error: str | None = None
    cost_usd: float | None = None
    # Code-level transparency: where in the codebase this call originated
    source_file: str | None = None
    source_line: int | None = None


class LlmOpStats(BaseModel):
    """Spend grouped by what kind of call it was, across every run, not one at a time.

    ``source_files`` names every distinct call site that logged this op, so a line
    here points back at the code that spent the tokens rather than only naming what
    it was for.
    """

    op: str
    calls: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_context_tokens: int
    avg_latency_ms: float
    error_count: int
    source_files: list[str] = []


class LlmReport(BaseModel):
    total_entries: int
    total_runs: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_context_tokens: int
    total_cost_usd: float
    avg_latency_ms: float
    models: list[LlmModelStats]
    runs: list[LlmRunSummary]
    ops: list[LlmOpStats] = []


class EvalAnswerTypeStats(BaseModel):
    """The judge's verdicts on the captured live-run corpus, by answer type.

    This is offline judgement over ``backend/tests/live_runs/``, the same fixtures
    ``scripts/eval_report.py`` ratchets against at gate time. The judge does not run
    against real production answers today, only against this corpus, so these numbers
    describe the corpus, not live traffic.
    """

    answer_type: str
    total_answers: int
    judged: int
    flagged: int
    known_inventions: int


class EvalAccuracyReport(BaseModel):
    total_fixtures: int
    total_answers: int
    judged: int
    flagged: int
    known_inventions: int
    by_answer_type: list[EvalAnswerTypeStats]


class LlmLedgerEntry(BaseModel):
    ts: str
    run_id: str | None = None
    op: str | None = None
    prompt: str | None = None
    tier: int | None = None
    model: str | None = None
    params_b: float | None = None
    local: bool | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    context_tokens: int | None = None
    latency_ms: int | None = None
    status: int | None = None
    error: str | None = None
    cost_usd: float | None = None
    # Code-level transparency: where in the codebase this call originated
    source_file: str | None = None
    source_line: int | None = None


class LlmLedger(BaseModel):
    entries: list[LlmLedgerEntry]
    total_entries: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_context_tokens: int
    total_cost_usd: float
