"""Request and response schemas for conducting a run."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.runs.enums import RunStatus
from app.runs.schemas import AnswerRead, MessageRead


class StartRunRequest(BaseModel):
    template_id: UUID


class RunMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


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
