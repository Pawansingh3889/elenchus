"""People's labels on recorded answers, and a judge model's verdicts beside them.

Labels on database answers hang off the answer and cascade with it, so withdrawing a run
takes them too. Labels on the committed corpus are keyed by fixture and answer position,
because those answers live in files; a script writes them back into the fixtures. Judge
verdicts are grouped by the judging that produced them, so each carries the prompt
version, the model and what that judging cost.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.evaluation.enums import EvalRunStatus, LabelVerdict
from app.workspaces.models import WorkspaceOwned

# One enum type in the database, shared by both label tables.
LABEL_VERDICT = SAEnum(LabelVerdict, name="label_verdict")


class AnswerLabel(WorkspaceOwned, Base):
    __tablename__ = "answer_labels"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    answer_id: Mapped[UUID] = mapped_column(
        ForeignKey("answers.id", ondelete="CASCADE"), unique=True
    )
    verdict: Mapped[LabelVerdict] = mapped_column(LABEL_VERDICT)
    note: Mapped[str | None] = mapped_column(Text, default=None)
    labelled_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    labelled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CorpusLabel(WorkspaceOwned, Base):
    __tablename__ = "corpus_labels"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "fixture",
            "answer_index",
            name="uq_corpus_labels_workspace_fixture_answer",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    fixture: Mapped[str] = mapped_column(String(128))
    answer_index: Mapped[int] = mapped_column(Integer)
    verdict: Mapped[LabelVerdict] = mapped_column(LABEL_VERDICT)
    note: Mapped[str | None] = mapped_column(Text, default=None)
    labelled_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    labelled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class JudgeRun(WorkspaceOwned, Base):
    """One judging of a run's answers: one model call, with what it cost."""

    __tablename__ = "judge_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("survey_runs.id", ondelete="CASCADE"), index=True
    )
    prompt_version: Mapped[str] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(128), default=None)
    tier: Mapped[int | None] = mapped_column(SmallInteger, default=None)
    answers: Mapped[int] = mapped_column(Integer)
    flagged: Mapped[int] = mapped_column(Integer)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(14, 8))
    # Calls that reported no usage: the cost above is then a floor.
    unmetered_calls: Mapped[int] = mapped_column(Integer)
    duration_ms: Mapped[int] = mapped_column(Integer)
    judged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class JudgeVerdict(WorkspaceOwned, Base):
    __tablename__ = "judge_verdicts"
    __table_args__ = (
        UniqueConstraint("judge_run_id", "answer_id", name="uq_judge_verdicts_run_answer"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    judge_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("judge_runs.id", ondelete="CASCADE"), index=True
    )
    answer_id: Mapped[UUID] = mapped_column(
        ForeignKey("answers.id", ondelete="CASCADE"), index=True
    )
    supported: Mapped[bool] = mapped_column(Boolean)
    why: Mapped[str] = mapped_column(Text)


class EvalRun(WorkspaceOwned, Base):
    """One scripted scenario, run through the real engine as part of a capped batch."""

    __tablename__ = "eval_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    batch_id: Mapped[UUID] = mapped_column(index=True)
    # Order within the batch: scenarios run one after another, in the order asked for.
    position: Mapped[int] = mapped_column(Integer)
    scenario: Mapped[str] = mapped_column(String(32))
    tier: Mapped[int] = mapped_column(SmallInteger)
    # The model that actually answered, read from the replies once the run is over.
    model: Mapped[str | None] = mapped_column(String(128), default=None)
    prompt_version: Mapped[str] = mapped_column(String(64))
    status: Mapped[EvalRunStatus] = mapped_column(SAEnum(EvalRunStatus, name="eval_run_status"))
    # The batch's cap, repeated on every row so a row explains itself.
    cap_usd: Mapped[Decimal] = mapped_column(Numeric(14, 8))
    # Kept when the conversation is withdrawn: the finding outlives the transcript.
    run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("survey_runs.id", ondelete="SET NULL"), default=None, index=True
    )
    template_id: Mapped[UUID | None] = mapped_column(default=None)
    turns: Mapped[int] = mapped_column(Integer, default=0)
    answers: Mapped[int] = mapped_column(Integer, default=0)
    hard_failures: Mapped[int] = mapped_column(Integer, default=0)
    soft_failures: Mapped[int] = mapped_column(Integer, default=0)
    checks: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(14, 8), default=Decimal("0"))
    unmetered_calls: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, default=None)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    # Moved on every turn, so a run the process abandoned mid-way reads as stale.
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
