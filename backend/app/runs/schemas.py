"""Read schemas for runs.

The transcript and answer shapes live here with the models they describe; conducting
and results both read them.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.runs.enums import AnswerKind, MessageRole, RunStatus
from app.templates.enums import TemplateStatus


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: MessageRole
    content: str
    created_at: datetime


class AnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question_id: UUID
    kind: AnswerKind
    question_text: str
    value: dict[str, Any]
    answered_at: datetime


class RunSummary(BaseModel):
    id: UUID
    respondent_name: str
    status: RunStatus
    version: int
    answered: int
    total: int
    started_at: datetime
    completed_at: datetime | None


class RunDetail(BaseModel):
    id: UUID
    respondent_name: str
    status: RunStatus
    version: int
    started_at: datetime
    completed_at: datetime | None
    messages: list[MessageRead]
    answers: list[AnswerRead]
    # Follow-ups the engine issued, per question id. The cap is spent when a probe is
    # asked, not when a reply to one is recorded, so this is the only faithful record of
    # follow-up spend: a probe that drew out the scripted answer itself leaves no
    # follow-up answer row behind, and the results view would show no sign of it.
    follow_ups_asked: dict[UUID, int] = Field(default_factory=dict)
    # Null until an author asks for one; the stretch AI summary is generated on request,
    # not as a side effect of the respondent finishing.
    summary: dict[str, Any] | None = None


class DashboardRow(BaseModel):
    """One survey as the author's dashboard shows it: what it is, and how it is going."""

    id: UUID
    title: str
    status: TemplateStatus
    updated_at: datetime
    closed_at: datetime | None

    started: int
    completed: int
    in_progress: int
    abandoned: int
    last_started_at: datetime | None
    last_completed_at: datetime | None

    @computed_field  # type: ignore[prop-decorator]  # pydantic needs the property last
    @property
    def completion_rate(self) -> float | None:
        """Completed as a share of started, or None when nobody has started.

        A property rather than a stored column: it is arithmetic on two numbers already
        here, and computing it in SQL would mean deciding there what 0/0 means. None says
        "no answer yet" honestly, where 0.0 would read as "everyone abandoned".
        """
        return self.completed / self.started if self.started else None
