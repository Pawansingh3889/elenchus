"""Request and response schemas for conducting a run."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.runs.enums import AnswerKind, MessageRole, RunStatus


class StartRunRequest(BaseModel):
    template_id: UUID


class RunMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


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


class CurrentQuestion(BaseModel):
    id: UUID
    text: str
    answer_type: str
    options: list[str]
    allow_other: bool
    required: bool


class RunRead(BaseModel):
    id: UUID
    status: RunStatus
    current_question: CurrentQuestion | None
    answered: int
    total: int
    messages: list[MessageRead]
    answers: list[AnswerRead]
