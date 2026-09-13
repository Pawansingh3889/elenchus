"""People's labels on recorded answers, and a judge model's verdicts beside them.

Labels on database answers hang off the answer and cascade with it, so withdrawing a run
takes them too. Labels on the committed corpus are keyed by fixture and answer position,
because those answers live in files; a script writes them back into the fixtures. Judge
verdicts are grouped by the judging that produced them, so each carries the prompt
version, the model and what that judging cost.
"""

from datetime import datetime
from decimal import Decimal
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
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.evaluation.enums import LabelVerdict

# One enum type in the database, shared by both label tables.
LABEL_VERDICT = SAEnum(LabelVerdict, name="label_verdict")


class AnswerLabel(Base):
    __tablename__ = "answer_labels"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    answer_id: Mapped[UUID] = mapped_column(
        ForeignKey("answers.id", ondelete="CASCADE"), unique=True
    )
    verdict: Mapped[LabelVerdict] = mapped_column(LABEL_VERDICT)
    note: Mapped[str | None] = mapped_column(Text, default=None)
    labelled_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    labelled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CorpusLabel(Base):
    __tablename__ = "corpus_labels"
    __table_args__ = (
        UniqueConstraint("fixture", "answer_index", name="uq_corpus_labels_fixture_answer"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    fixture: Mapped[str] = mapped_column(String(128))
    answer_index: Mapped[int] = mapped_column(Integer)
    verdict: Mapped[LabelVerdict] = mapped_column(LABEL_VERDICT)
    note: Mapped[str | None] = mapped_column(Text, default=None)
    labelled_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    labelled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class JudgeRun(Base):
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


class JudgeVerdict(Base):
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
