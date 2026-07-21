"""Read schemas for runs.

The transcript and answer shapes live here with the models they describe; conducting
and results both read them.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.runs.enums import AnswerKind, MessageRole, RunStatus


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
