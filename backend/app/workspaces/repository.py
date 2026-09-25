"""Workspace settings and retention deletion queries."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Connection, bindparam, case, delete, event, func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, SessionTransaction

from app.db.base import Base
from app.errors import UnauthorizedError
from app.runs.enums import MessageRole, RunStatus
from app.runs.models import RunMessage, SurveyRun
from app.workspaces.context import current_workspace
from app.workspaces.models import (
    EmployeeRosterEntry,
    ResponseDeletionAudit,
    ResponseUsageTotal,
    Workspace,
    WorkspaceAccessChange,
    WorkspaceInvitation,
    WorkspaceRetentionChange,
)


@event.listens_for(Session, "after_begin")
def _apply_workspace(
    session: Session, transaction: SessionTransaction, connection: Connection
) -> None:
    workspace_id = session.info.get("workspace_id")
    if workspace_id is not None:
        connection.execute(
            text("SELECT set_config('app.workspace_id', :workspace, true)"),
            {"workspace": str(workspace_id)},
        )


@dataclass(frozen=True)
class ExpiredRun:
    run: SurveyRun
    activity_at: datetime
    expires_at: datetime


class WorkspaceRepository:
    """Transaction-local workspace context, identity resolution, and retention queries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bind(self, workspace_id: UUID) -> None:
        current = self.session.info.get("workspace_id")
        if current is not None and current != workspace_id:
            raise UnauthorizedError("A session cannot change company workspace.")
        self.session.info["workspace_id"] = workspace_id
        current_workspace.set(workspace_id)
        await self.session.execute(
            text("SELECT set_config('app.workspace_id', :workspace, true)"),
            {"workspace": str(workspace_id)},
        )

    async def resolve_identity(
        self,
        *,
        user_id: UUID | None = None,
        email: str | None = None,
        microsoft_id: str | None = None,
    ) -> bool:
        """Bind one validated identity's workspace before normal tenant queries begin."""
        from app.users.models import User

        if sum(value is not None for value in (user_id, email, microsoft_id)) != 1:
            raise ValueError("Exactly one authenticated identity is required.")
        await self.session.execute(
            text(
                "SELECT set_config('app.actor_id', :actor, true), "
                "set_config('app.verified_email', :email, true), "
                "set_config('app.microsoft_id', :microsoft, true)"
            ),
            {
                "actor": str(user_id) if user_id is not None else "",
                "email": email or "",
                "microsoft": microsoft_id or "",
            },
        )
        try:
            if user_id is not None:
                criterion = User.id == user_id
            elif microsoft_id is not None:
                criterion = User.microsoft_id == microsoft_id
            else:
                criterion = User.email == email
            workspace = await self.session.scalar(select(User.workspace_id).where(criterion))
        finally:
            await self.session.execute(
                text(
                    "SELECT set_config('app.actor_id', '', true), "
                    "set_config('app.verified_email', '', true), "
                    "set_config('app.microsoft_id', '', true)"
                )
            )
        if workspace is None:
            return False
        await self.bind(workspace)
        return True

    async def verify_runtime_role(self) -> None:
        """Reject production roles that can bypass the tenant policies."""
        bypasses = await self.session.scalar(
            text("SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user")
        )
        if bypasses is not False:
            raise RuntimeError(
                "Production DATABASE_URL must use a non-superuser without BYPASSRLS."
            )
        tables = tuple(Base.metadata.tables)
        safe_tables = await self.session.scalar(
            text(
                "SELECT count(*) FROM pg_class WHERE relnamespace = 'public'::regnamespace "
                "AND relname IN :tables AND relrowsecurity AND relforcerowsecurity "
                "AND NOT pg_has_role(current_user, relowner, 'MEMBER')"
            ).bindparams(bindparam("tables", expanding=True)),
            {"tables": tables},
        )
        if safe_tables != len(tables):
            raise RuntimeError(
                "Production tables must enforce workspace policies and belong to a separate "
                "deployment role."
            )

    async def get_workspace(self) -> Workspace | None:
        workspace_id = self.session.info.get("workspace_id")
        if workspace_id is None:
            return None
        return await self.session.get(Workspace, workspace_id)

    async def latest_retention_change(self) -> WorkspaceRetentionChange | None:
        stmt = (
            select(WorkspaceRetentionChange)
            .order_by(
                WorkspaceRetentionChange.changed_at.desc(),
                WorkspaceRetentionChange.id.desc(),
            )
            .limit(1)
        )
        return (await self.session.scalars(stmt)).first()

    def add_retention_change(self, change: WorkspaceRetentionChange) -> None:
        self.session.add(change)

    async def expired_runs(self, now: datetime, limit: int) -> list[ExpiredRun]:
        last_user_activity = (
            select(func.max(RunMessage.created_at))
            .where(
                RunMessage.run_id == SurveyRun.id,
                RunMessage.role == MessageRole.user,
            )
            .correlate(SurveyRun)
            .scalar_subquery()
        )
        activity_at = func.coalesce(last_user_activity, SurveyRun.started_at)
        anchor = case(
            (
                SurveyRun.status == RunStatus.completed,
                func.coalesce(SurveyRun.completed_at, SurveyRun.started_at),
            ),
            else_=activity_at,
        )
        expires_at = anchor + (Workspace.response_retention_days * text("interval '1 day'"))
        stmt = (
            select(SurveyRun, activity_at.label("activity_at"), expires_at.label("expires_at"))
            .join(Workspace, Workspace.id == SurveyRun.workspace_id)
            .where(expires_at <= now)
            .order_by(expires_at)
            .limit(limit)
        )
        return [
            ExpiredRun(run=run, activity_at=activity, expires_at=expires)
            for run, activity, expires in (await self.session.execute(stmt)).all()
        ]

    async def delete_run(self, run_id: UUID) -> None:
        await self.session.execute(delete(SurveyRun).where(SurveyRun.id == run_id))

    async def add_usage(
        self,
        month_start: date,
        *,
        completed_responses: int,
        deleted_runs: int,
        llm_calls: int,
        llm_prompt_tokens: int,
        llm_completion_tokens: int,
        llm_unmetered_calls: int,
        llm_cost_usd: Decimal,
    ) -> None:
        values: dict[str, Any] = {
            "month_start": month_start,
            "completed_responses": completed_responses,
            "deleted_runs": deleted_runs,
            "llm_calls": llm_calls,
            "llm_prompt_tokens": llm_prompt_tokens,
            "llm_completion_tokens": llm_completion_tokens,
            "llm_unmetered_calls": llm_unmetered_calls,
            "llm_cost_usd": llm_cost_usd,
        }
        stmt = insert(ResponseUsageTotal).values(values)
        excluded = stmt.excluded
        stmt = stmt.on_conflict_do_update(
            index_elements=[ResponseUsageTotal.workspace_id, ResponseUsageTotal.month_start],
            set_={
                "completed_responses": ResponseUsageTotal.completed_responses
                + excluded.completed_responses,
                "deleted_runs": ResponseUsageTotal.deleted_runs + excluded.deleted_runs,
                "llm_calls": ResponseUsageTotal.llm_calls + excluded.llm_calls,
                "llm_prompt_tokens": ResponseUsageTotal.llm_prompt_tokens
                + excluded.llm_prompt_tokens,
                "llm_completion_tokens": ResponseUsageTotal.llm_completion_tokens
                + excluded.llm_completion_tokens,
                "llm_unmetered_calls": ResponseUsageTotal.llm_unmetered_calls
                + excluded.llm_unmetered_calls,
                "llm_cost_usd": ResponseUsageTotal.llm_cost_usd + excluded.llm_cost_usd,
            },
        )
        await self.session.execute(stmt)

    def add_deletion_audit(self, audit: ResponseDeletionAudit) -> None:
        self.session.add(audit)

    async def invitation_by_email(self, email: str) -> WorkspaceInvitation | None:
        stmt = select(WorkspaceInvitation).where(WorkspaceInvitation.email == email)
        return (await self.session.scalars(stmt)).first()

    async def list_invitations(self) -> list[WorkspaceInvitation]:
        stmt = select(WorkspaceInvitation).order_by(WorkspaceInvitation.invited_at.desc())
        return list((await self.session.scalars(stmt)).all())

    def add_invitation(self, invitation: WorkspaceInvitation) -> None:
        self.session.add(invitation)

    async def roster_by_email(self, email: str) -> EmployeeRosterEntry | None:
        stmt = select(EmployeeRosterEntry).where(EmployeeRosterEntry.email == email)
        return (await self.session.scalars(stmt)).first()

    async def list_roster(self) -> list[EmployeeRosterEntry]:
        stmt = select(EmployeeRosterEntry).order_by(EmployeeRosterEntry.email)
        return list((await self.session.scalars(stmt)).all())

    def add_roster_entry(self, entry: EmployeeRosterEntry) -> None:
        self.session.add(entry)

    def add_access_change(self, change: WorkspaceAccessChange) -> None:
        self.session.add(change)

    async def access_history(self, email: str | None = None) -> list[WorkspaceAccessChange]:
        stmt = select(WorkspaceAccessChange).order_by(
            WorkspaceAccessChange.changed_at.desc(), WorkspaceAccessChange.id.desc()
        )
        if email is not None:
            stmt = stmt.where(WorkspaceAccessChange.email == email)
        return list((await self.session.scalars(stmt.limit(200))).all())
