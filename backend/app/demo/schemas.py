"""Validated public and operator demo requests."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.users.schemas import UserRead


class IssuePass(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

    @field_validator("company", "name", "email")
    @classmethod
    def readable(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Must not be blank.")
        return value


class PassRead(BaseModel):
    workspace_id: UUID
    pass_token: str
    expires_at: datetime | None


class EnterPass(BaseModel):
    token: str = Field(min_length=20, max_length=1000)


class EnterSurvey(EnterPass):
    consent: Literal[True]


class Entered(BaseModel):
    user: UserRead
    template_id: UUID | None = None
    run_id: UUID | None = None


class ShareRead(BaseModel):
    token: str
    expires_at: datetime


class SurveyEntryRead(BaseModel):
    title: str
    description: str | None
    questions: int
    remaining_sessions: int | None
    disclosure: str


class AccessRead(BaseModel):
    workspace_id: UUID
    company: str
    mode: Literal["standard", "demo", "customer"]
    active: bool
    expires_at: datetime | None
    surveys_created: int
    survey_limit: int | None
    question_limit: int | None
    session_limit_per_survey: int | None
    monthly_response_allowance: int | None
    sessions_started_this_month: int
    product: str | None


class ActivateCustomer(BaseModel):
    product: str = Field(min_length=1, max_length=200)
    purchase_type: Literal["subscription", "one_time"]
    valid_until: datetime | None = None
    monthly_response_allowance: int = Field(ge=1, le=100000)
    purchase_verified: Literal[True]

    @model_validator(mode="after")
    def valid_purchase(self) -> "ActivateCustomer":
        if not self.product.strip():
            raise ValueError("Name the purchased product.")
        if self.purchase_type == "subscription" and self.valid_until is None:
            raise ValueError("An active subscription needs its current paid-through date.")
        if self.purchase_type == "one_time" and self.valid_until is not None:
            raise ValueError("One-time purchases qualify permanently; omit the expiry.")
        if self.valid_until is not None and self.valid_until.tzinfo is None:
            raise ValueError("The paid-through date must include a timezone.")
        return self


class OperatorWorkspace(BaseModel):
    workspace_id: UUID
    company: str
    email: str
    issued_at: datetime
    activated_at: datetime | None
    access: AccessRead


class OperatorRead(BaseModel):
    workspaces: list[OperatorWorkspace]
    month: str
    budget_usd: float
    charged_or_reserved_usd: float
    known_spend_usd: float
    uncertain_attempts: int
    attempts: int
    failed_attempts: int
