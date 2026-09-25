"""A workspace is the data boundary for one customer company."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

LEGACY_WORKSPACE_ID = UUID("00000000-0000-0000-0000-000000000001")


class WorkspaceOwned:
    """Ownership is assigned from the authenticated transaction, never a request body."""

    workspace_id: Mapped[UUID] = mapped_column(
        ForeignKey("workspaces.id"),
        index=True,
        server_default=text("nullif(current_setting('app.workspace_id', true), '')::uuid"),
    )


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200))
    response_retention_days: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("90"), default=90
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkspaceRetentionChange(WorkspaceOwned, Base):
    """Append-only record of owner changes to the response retention policy."""

    __tablename__ = "workspace_retention_changes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    changed_by: Mapped[UUID | None] = mapped_column(default=None)
    before_days: Mapped[int] = mapped_column(Integer)
    after_days: Mapped[int] = mapped_column(Integer)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ResponseUsageTotal(WorkspaceOwned, Base):
    """Non-identifying monthly totals retained after response content is purged."""

    __tablename__ = "response_usage_totals"
    __table_args__ = (PrimaryKeyConstraint("workspace_id", "month_start"),)

    month_start: Mapped[date] = mapped_column(Date)
    completed_responses: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    deleted_runs: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    llm_calls: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    llm_prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    llm_completion_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    llm_unmetered_calls: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    llm_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(18, 8), default=Decimal("0"), server_default=text("0")
    )


class ResponseDeletionAudit(WorkspaceOwned, Base):
    """Non-content evidence that a response was removed by retention."""

    __tablename__ = "response_deletion_audits"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column()
    template_id: Mapped[UUID] = mapped_column()
    triggered_by: Mapped[UUID | None] = mapped_column(default=None)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    deleted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    usage: Mapped[dict[str, int | str]] = mapped_column(JSONB, default=dict, nullable=False)


class WorkspaceInvitation(WorkspaceOwned, Base):
    """An email explicitly invited into this pilot workspace."""

    __tablename__ = "workspace_invitations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    workspace_role: Mapped[str] = mapped_column(String(16))
    function: Mapped[str] = mapped_column(String(32))
    band: Mapped[str] = mapped_column(String(32))
    token_digest: Mapped[str] = mapped_column(String(64), unique=True)
    invited_by: Mapped[UUID] = mapped_column()
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class EmployeeRosterEntry(WorkspaceOwned, Base):
    """An approved employee address and its audience job, before first sign-in."""

    __tablename__ = "employee_roster"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    function: Mapped[str] = mapped_column(String(32))
    band: Mapped[str] = mapped_column(String(32))
    approved_by: Mapped[UUID] = mapped_column()
    approved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class WorkspaceAccessChange(WorkspaceOwned, Base):
    """Append-only audit record for invitations and roster eligibility."""

    __tablename__ = "workspace_access_changes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320))
    access_kind: Mapped[str] = mapped_column(String(16))
    action: Mapped[str] = mapped_column(String(16))
    changed_by: Mapped[UUID | None] = mapped_column(default=None)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
