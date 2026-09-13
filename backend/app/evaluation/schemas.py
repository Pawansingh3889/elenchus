"""What the evaluation lens reads and returns."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.evaluation.enums import EvalRunStatus, LabelVerdict

Source = Literal["corpus", "runs"]
MIN_CAP_USD = 0.000001


class EvalItem(BaseModel):
    """One recorded answer beside what was said, with any judge verdict and label."""

    # "corpus:<fixture>:<index>" or "answer:<uuid>": the handle a label is written against.
    key: str
    source: Source
    # The fixture's name, or the survey's title.
    origin: str
    run_id: UUID | None
    model: str | None
    when: str | None
    question_text: str
    answer_type: str
    options: list[str]
    kind: str
    value: dict[str, Any]
    said: list[str]
    judge_supported: bool | None
    judge_why: str | None
    judge_prompt: str | None
    # A corpus file's own hand-set mark; always false for database answers.
    marked_invented: bool
    label: LabelVerdict | None
    note: str | None
    labelled_at: datetime | None


class LabelRequest(BaseModel):
    verdict: LabelVerdict
    note: str | None = Field(default=None, max_length=2000)


class Rate(BaseModel):
    numerator: int
    denominator: int
    value: float | None
    low: float | None
    high: float | None
    too_few: bool


class FaithfulnessSlice(BaseModel):
    name: str
    items: int
    labelled: int
    supported: int
    invented: int
    unsure: int
    # Invented out of the answers labelled supported or invented.
    invention_rate: Rate
    # Over answers with both a decisive label and a judge verdict.
    judged_and_labelled: int
    # Of the answers the judge flagged, how many a person labelled invented.
    judge_precision: Rate
    # Of the answers a person labelled invented, how many the judge flagged.
    judge_recall: Rate
    # Of the answers a person labelled supported, how many the judge flagged anyway.
    judge_false_alarms: Rate


class FaithfulnessReport(BaseModel):
    min_labelled: int
    overall: FaithfulnessSlice
    by_source: list[FaithfulnessSlice]
    by_answer_type: list[FaithfulnessSlice]
    by_model: list[FaithfulnessSlice]


class JudgeRunRead(BaseModel):
    id: UUID
    run_id: UUID
    prompt_version: str
    model: str | None
    tier: int | None
    answers: int
    flagged: int
    # A number, like every other cost the lens reads; stored as NUMERIC.
    cost_usd: float
    unmetered_calls: int
    duration_ms: int
    judged_at: datetime


class Median(BaseModel):
    value: float | None
    # How many measurements the median is over.
    n: int


class QualitySlice(BaseModel):
    """How the conversations in one group went, measured, never judged."""

    name: str
    runs: int
    # Completed out of every run with a conversation in this group.
    completion: Rate
    answers: int
    # Answers that record a refusal, out of every recorded answer.
    declined: Rate
    # Per run: respondent messages for each recorded answer.
    turns_per_answer: Median
    # Per run: characters the respondent typed.
    respondent_chars: Median
    # Per completed run.
    minutes_to_complete: Median
    # Per traced turn: how long the respondent waited for the reply.
    wait_ms_per_turn: Median
    follow_ups_asked: int
    follow_up_answers: int
    # Per follow-up answer: the share of words in the reply that produced it that were not
    # in the reply behind the question's first answer. Near zero, the probe drew nothing.
    follow_up_new_words: Median
    # Per completed run.
    cost_per_completed_run: Median
    cost_per_answer: float | None
    # Calls that reported no usage: every cost above is then a floor.
    unmetered_calls: int


class QualityReport(BaseModel):
    # Runs with no respondent message at all, such as seeded sample data: counted, not
    # measured, because they are not conversations.
    runs_without_conversation: int
    overall: QualitySlice
    by_survey: list[QualitySlice]
    by_model: list[QualitySlice]
    by_prompt: list[QualitySlice]


class ScenarioRead(BaseModel):
    key: str
    title: str
    # For a drafted scenario, the count its brief asks for: the draft may differ.
    questions: int
    max_turns: int
    # Drafted from a brief by the pinned tier before the conversation, at a cost.
    generated: bool


class TierRead(BaseModel):
    tier: int
    model: str


class EvalOptions(BaseModel):
    scenarios: list[ScenarioRead]
    tiers: list[TierRead]
    prompt_versions: list[str]
    active_prompt: str


class EvalStartRequest(BaseModel):
    scenarios: list[str] = Field(min_length=1, max_length=11)
    tier: int = Field(ge=1, le=4)
    # None runs the conduct prompt that is active right now.
    prompt_version: str | None = None
    # The most the whole batch may spend; it stops at the turn that reaches this. The floor
    # is one the column holds exactly: a smaller cap was stored as zero and every scenario
    # in the batch was capped before it began.
    cap_usd: float = Field(ge=MIN_CAP_USD, le=25)


class CheckRead(BaseModel):
    name: str
    ok: bool
    hard: bool
    detail: Any


class EvalRunRead(BaseModel):
    id: UUID
    batch_id: UUID
    position: int
    scenario: str
    tier: int
    model: str | None
    prompt_version: str
    status: EvalRunStatus
    cap_usd: float
    run_id: UUID | None
    template_id: UUID | None
    turns: int
    answers: int
    hard_failures: int
    soft_failures: int
    checks: list[CheckRead]
    cost_usd: float
    unmetered_calls: int
    duration_ms: int
    error: str | None
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    heartbeat_at: datetime | None
    # Running, but not heard from in a while: the process that ran it has probably gone.
    stale: bool


class ComparisonGroup(BaseModel):
    """Completed evaluation runs of one model under one conduct prompt version."""

    name: str
    model: str
    prompt_version: str
    runs: int
    # Runs where no hard check failed, out of the completed runs.
    clean_runs: Rate
    # Hard checks that passed, out of every hard check in those runs. Soft checks turn on
    # judgement and are left out of accuracy for the reason they are soft.
    hard_checks: Rate
    cost_per_run: Median
    duration_ms: Median
    turns: Median
    # Calls in these runs that reported no usage, so a cost here is a floor when non-zero.
    unmetered_calls: int
    scenarios: list[str]


class ComparisonCell(BaseModel):
    """One scenario under one group: the matrix a comparison is read from."""

    scenario: str
    group: str
    runs: int
    clean_runs: int
    cost_per_run: Median
    duration_ms: Median


class Agreement(BaseModel):
    """How often Qwen picked the tool the hosted model called, beside what followed.

    Qwen3-0.6B's reading of the same prompt, never the hosted model's internals. Only
    readings of an attempt the engine checked count toward the rates.
    """

    analysed: int
    agrees: Rate
    when_accepted: Rate
    when_refused: Rate
    # Accepted record_answer calls, by how a person labelled the answer they recorded.
    on_supported: Rate
    on_invented: Rate


class ComparisonReport(BaseModel):
    completed_runs: int
    # Capped, failed, queued or running: no finished transcript, so not scored.
    left_out: int
    groups: list[ComparisonGroup]
    cells: list[ComparisonCell]
    agreement: Agreement
