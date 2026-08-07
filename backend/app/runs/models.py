"""Run, answer, and transcript-message models.

The conduct engine owns run state: ``current_question_index`` is advanced by code,
never by the model. ``answers.question_id`` refers to a question id inside the frozen
version definition (not a FK to the mutable ``survey_questions``); follow-up answers
carry their model-invented ``question_text`` denormalised.
"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.runs.enums import AnswerKind, MessageRole, RunStatus

if TYPE_CHECKING:
    from app.llm.ledger import Spend as LLMSpend

# Replies share the ``probes_asked`` JSONB with follow-ups, under this prefix — same
# lifecycle, no extra column, and a question id (a UUID) can never collide with it.
# Defined beside the column so the engine that writes it and the results service that
# reads it cannot drift apart on the spelling.
REPLY_PREFIX = "reply:"


class SurveyRun(Base):
    __tablename__ = "survey_runs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    template_version_id: Mapped[UUID] = mapped_column(ForeignKey("survey_template_versions.id"))
    respondent_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[RunStatus] = mapped_column(
        SAEnum(RunStatus, name="run_status"), default=RunStatus.in_progress
    )
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)
    # The language this run is conducted in, fixed when it starts. Fixed rather than
    # read per request because a respondent who resumes on another device, or after
    # their browser's language changed, must not find the interview switching language
    # mid-conversation: the transcript above them is already in the first one.
    language: Mapped[str] = mapped_column(String(8), default="en", server_default="en")
    # Follow-ups *asked* per question id. The cap is spent when the engine issues a
    # probe, not when a reply to one is recorded — otherwise a respondent who never
    # answers a probe is never charged for it and can be probed indefinitely.
    probes_asked: Mapped[dict[str, int]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), default=dict
    )
    # What this run has cost in model calls so far, accumulated turn by turn (and by its
    # AI summary, which is spent on this run as surely as any turn). Denormalised from
    # the JSONL ledger on purpose: the ledger is the record for offline analysis and is
    # not something a request should be parsing, and these answer "what did this
    # conversation cost" without leaving the database.
    #
    # Counts stay separate rather than summed, because input and output tokens are priced
    # differently everywhere and a single total cannot be re-priced later.
    llm_calls: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    llm_prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    llm_completion_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    # Calls whose tokens or cost the provider never reported. Kept beside the sums so a
    # total can say "at least": without it, unknown folds into zero and a tier that
    # omits usage reads as free, which is the one number that is certainly wrong.
    llm_unmetered_calls: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    # Numeric, not float: this is money, it is summed across runs for a bill, and binary
    # floating point drifts. 8 decimal places holds a single cheap local call.
    llm_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(18, 8), default=Decimal("0"), server_default=text("0")
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    # Stretch: structured AI summary of the completed run.
    summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)

    answers: Mapped[list["Answer"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="Answer.answered_at"
    )
    messages: Mapped[list["RunMessage"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="RunMessage.created_at"
    )


def add_llm_spend(run: SurveyRun, spend: "LLMSpend") -> None:
    """Fold one measured block of model calls into the run's running totals.

    Lives beside the columns it writes so the conduct engine and the summary service
    cannot drift on how the fold is done. The cost crosses into ``Decimal`` here and
    stays there: it arrives as a float because that is what a rate times a token count
    is, but it is money from this point on. ``str`` rather than ``Decimal(float)``,
    which would carry the float's binary tail into the exact type and defeat the point
    of using it.
    """
    run.llm_calls += spend.calls
    run.llm_prompt_tokens += spend.prompt_tokens
    run.llm_completion_tokens += spend.completion_tokens
    run.llm_unmetered_calls += spend.unmetered_calls
    run.llm_cost_usd += Decimal(str(spend.cost_usd))


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("survey_runs.id", ondelete="CASCADE"))
    # Question id from the frozen version definition — intentionally not a FK.
    question_id: Mapped[UUID] = mapped_column()
    kind: Mapped[AnswerKind] = mapped_column(SAEnum(AnswerKind, name="answer_kind"))
    question_text: Mapped[str] = mapped_column(Text)
    # Shaped per answer_type, e.g. {"option": "..."} or {"rating": 4}.
    value: Mapped[dict[str, Any]] = mapped_column(JSONB)
    answered_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    # Client-side for the same reason as the transcript: Postgres now() is transaction
    # time, so answers written in one turn would tie and order arbitrarily.
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(UTC)
    )

    run: Mapped["SurveyRun"] = relationship(back_populates="answers")


class RunMessage(Base):
    __tablename__ = "run_messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("survey_runs.id", ondelete="CASCADE"))
    role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole, name="message_role"))
    content: Mapped[str] = mapped_column(Text)
    # Stamped client-side: Postgres now() is transaction time, so a question and the
    # answer written in the same transaction would tie and the transcript would scramble.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(UTC)
    )
    answer_id: Mapped[UUID | None] = mapped_column(ForeignKey("answers.id"), default=None)

    run: Mapped["SurveyRun"] = relationship(back_populates="messages")
