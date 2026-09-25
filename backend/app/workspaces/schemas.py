"""Request and response schemas for company retention settings."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.users.models import Band, Function, WorkspaceRole


class RetentionRead(BaseModel):
    retention_days: int
    default_days: int = 90
    changed_at: datetime | None = None


class RetentionUpdate(BaseModel):
    retention_days: int = Field(ge=1, le=3650)
    confirm_shorter: bool = False


class RetentionPurgeRead(BaseModel):
    deleted_runs: int
    deleted_completed_responses: int
    retained_usage_months: int


class InvitationCreate(BaseModel):
    email: str = Field(max_length=320)
    display_name: str = Field(max_length=200)
    workspace_role: WorkspaceRole
    function: Function
    band: Band
    expires_in_days: int = Field(default=7, ge=1, le=30)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().casefold()
        if not normalized:
            raise ValueError("An email address is required.")
        return normalized

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("A display name is required.")
        return normalized

    @field_validator("workspace_role")
    @classmethod
    def owner_cannot_be_invited(cls, value: WorkspaceRole) -> WorkspaceRole:
        if value is WorkspaceRole.owner:
            raise ValueError("The workspace owner must be transferred explicitly.")
        return value


class InvitationRead(BaseModel):
    id: UUID
    email: str
    display_name: str
    workspace_role: WorkspaceRole
    function: Function
    band: Band
    invited_by: UUID
    invited_at: datetime
    expires_at: datetime
    accepted_at: datetime | None
    revoked_at: datetime | None
    token: str | None = None


class RosterCreate(BaseModel):
    email: str = Field(max_length=320)
    display_name: str = Field(max_length=200)
    function: Function
    band: Band

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().casefold()
        if not normalized:
            raise ValueError("An email address is required.")
        return normalized

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("A display name is required.")
        return normalized


class RosterRead(BaseModel):
    id: UUID
    email: str
    display_name: str
    function: Function
    band: Band
    approved_by: UUID
    approved_at: datetime
    revoked_at: datetime | None


class AccessChangeRead(BaseModel):
    id: UUID
    email: str
    access_kind: str
    action: str
    changed_by: UUID | None
    changed_at: datetime
    details: dict[str, object]
