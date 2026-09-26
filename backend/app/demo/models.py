"""Persistent access and allowance records. Deleting content never restores usage."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.workspaces.models import WorkspaceOwned

PLATFORM_WORKSPACE_ID = UUID("00000000-0000-0000-0000-000000000002")


class DemoAccess(WorkspaceOwned, Base):
    __tablename__ = "demo_access"
    __table_args__ = (UniqueConstraint("workspace_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    pass_digest: Mapped[str] = mapped_column(String(64))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    surveys_created: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    customer_product: Mapped[str | None] = mapped_column(String(200), default=None)
    customer_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    monthly_response_allowance: Mapped[int | None] = mapped_column(Integer, default=None)
    approved_by: Mapped[str | None] = mapped_column(String(320), default=None)


class DemoRegistry(WorkspaceOwned, Base):
    """Operator directory in the platform workspace, containing no respondent content."""

    __tablename__ = "demo_registry"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(200))
    contact_email: Mapped[str] = mapped_column(String(320))
    issued_by: Mapped[str] = mapped_column(String(320))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DemoUsage(WorkspaceOwned, Base):
    __tablename__ = "demo_usage"
    __table_args__ = (UniqueConstraint("workspace_id", "month_start"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    month_start: Mapped[date] = mapped_column(Date)
    sessions_started: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))


class DemoSpend(WorkspaceOwned, Base):
    """Reserve before transport. A crash or missing usage leaves the reservation charged."""

    __tablename__ = "demo_spend"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    demo_workspace_id: Mapped[UUID]
    month_start: Mapped[date] = mapped_column(Date, index=True)
    model: Mapped[str] = mapped_column(String(200))
    reserved_usd: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    actual_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), default=None)
    failed: Mapped[bool | None] = mapped_column(default=None)
    latency_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
