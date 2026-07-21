"""Pydantic v2 request/response schemas for templates."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.templates.enums import AnswerType, TemplateStatus

SELECT_TYPES = {AnswerType.single_select, AnswerType.multi_select}


class QuestionInput(BaseModel):
    text: str = Field(min_length=1)
    answer_type: AnswerType
    options: list[str] = Field(default_factory=list)
    allow_other: bool = False
    required: bool = True
    allow_follow_ups: bool = False

    @model_validator(mode="after")
    def _check_options(self) -> "QuestionInput":
        if self.answer_type in SELECT_TYPES:
            if not self.options:
                raise ValueError(f"{self.answer_type.value} requires at least one option")
        elif self.options:
            raise ValueError(f"{self.answer_type.value} must not carry options")
        return self


class TemplateWrite(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    questions: list[QuestionInput] = Field(default_factory=list)


# Create and update share the same shape (a full draft), but stay distinct types
# so the API and future divergence read clearly.
class TemplateCreate(TemplateWrite):
    pass


class TemplateUpdate(TemplateWrite):
    pass


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    position: int
    text: str
    answer_type: AnswerType
    options: list[str]
    allow_other: bool
    required: bool
    allow_follow_ups: bool


class TemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    status: TemplateStatus
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    questions: list[QuestionRead]


class TemplateSummary(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: TemplateStatus
    updated_at: datetime
    question_count: int


class TemplateVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    template_id: UUID
    version: int
    published_at: datetime
