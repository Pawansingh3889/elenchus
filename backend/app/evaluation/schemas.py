"""What the evaluation lens reads and returns."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.evaluation.enums import LabelVerdict

Source = Literal["corpus", "runs"]


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
