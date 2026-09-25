"""Retention settings and response-content expiry."""

import hashlib
import secrets
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.access import is_workspace_admin, is_workspace_owner
from app.embeddings.repository import EmbeddingRepository
from app.embeddings.service import digest
from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.interp.repository import InterpRepository
from app.runs.enums import RunStatus
from app.trace.repository import SpanRepository
from app.users.models import Band, Function, User, WorkspaceRole
from app.workspaces.models import (
    EmployeeRosterEntry,
    ResponseDeletionAudit,
    WorkspaceAccessChange,
    WorkspaceInvitation,
    WorkspaceRetentionChange,
)
from app.workspaces.repository import WorkspaceRepository
from app.workspaces.schemas import (
    AccessChangeRead,
    InvitationCreate,
    InvitationRead,
    RetentionPurgeRead,
    RetentionRead,
    RetentionUpdate,
    RosterCreate,
    RosterRead,
)


class WorkspaceService:
    DEFAULT_RETENTION_DAYS = 90

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = WorkspaceRepository(session)

    async def retention(self) -> RetentionRead:
        workspace = await self.repo.get_workspace()
        if workspace is None:
            raise NotFoundError("Workspace not found.")
        change = await self.repo.latest_retention_change()
        return RetentionRead(
            retention_days=workspace.response_retention_days,
            default_days=self.DEFAULT_RETENTION_DAYS,
            changed_at=change.changed_at if change else None,
        )

    async def update_retention(self, data: RetentionUpdate, owner: User) -> RetentionRead:
        if not is_workspace_owner(owner):
            raise ForbiddenError("Only the workspace owner can change retention.")
        workspace = await self.repo.get_workspace()
        if workspace is None:
            raise NotFoundError("Workspace not found.")
        before = workspace.response_retention_days
        if data.retention_days < before and not data.confirm_shorter:
            raise ConflictError(
                "Shortening retention applies to existing responses and requires confirmation."
            )
        if data.retention_days != before:
            workspace.response_retention_days = data.retention_days
            self.repo.add_retention_change(
                WorkspaceRetentionChange(
                    changed_by=owner.id,
                    before_days=before,
                    after_days=data.retention_days,
                )
            )
            await self.session.commit()
        return await self.retention()

    async def purge_expired(self, actor: User, *, limit: int = 100) -> RetentionPurgeRead:
        if not is_workspace_admin(actor):
            raise ForbiddenError("This action requires a workspace owner or admin.")
        if not 1 <= limit <= 1000:
            raise ConflictError("Retention purge batch size must be between 1 and 1000.")
        now = datetime.now(UTC)
        expired = await self.repo.expired_runs(now, limit)
        if not expired:
            return RetentionPurgeRead(
                deleted_runs=0,
                deleted_completed_responses=0,
                retained_usage_months=0,
            )

        spans = SpanRepository(self.session)
        interp = InterpRepository(self.session)
        vectors = EmbeddingRepository(self.session)
        usage_by_month: dict[date, dict[str, int]] = defaultdict(
            lambda: {
                "completed_responses": 0,
                "deleted_runs": 0,
                "llm_calls": 0,
                "llm_prompt_tokens": 0,
                "llm_completion_tokens": 0,
                "llm_unmetered_calls": 0,
            }
        )
        cost_by_month: dict[date, Decimal] = defaultdict(Decimal)
        deleted_completed = 0
        for candidate in expired:
            run = candidate.run
            anchor = run.completed_at or candidate.activity_at
            month_start = date(anchor.year, anchor.month, 1)
            usage = usage_by_month[month_start]
            usage["completed_responses"] += int(run.status is RunStatus.completed)
            usage["deleted_runs"] += 1
            usage["llm_calls"] += run.llm_calls
            usage["llm_prompt_tokens"] += run.llm_prompt_tokens
            usage["llm_completion_tokens"] += run.llm_completion_tokens
            usage["llm_unmetered_calls"] += run.llm_unmetered_calls
            cost_by_month[month_start] += run.llm_cost_usd
            if run.status is RunStatus.completed:
                deleted_completed += 1

            texts = await vectors.run_texts(run.id)
            await spans.delete_for_run(run.id)
            await interp.delete_for_run(run.id)
            await vectors.delete_digests([digest(text) for text in texts])
            self.repo.add_deletion_audit(
                ResponseDeletionAudit(
                    run_id=run.id,
                    template_id=run.template_id,
                    triggered_by=actor.id,
                    started_at=run.started_at,
                    activity_at=candidate.activity_at,
                    completed_at=run.completed_at,
                    usage={
                        "completed": int(run.status is RunStatus.completed),
                        "llm_calls": run.llm_calls,
                    },
                )
            )
            await self.repo.delete_run(run.id)

        for month_start, usage in usage_by_month.items():
            await self.repo.add_usage(
                month_start,
                completed_responses=int(usage["completed_responses"]),
                deleted_runs=int(usage["deleted_runs"]),
                llm_calls=int(usage["llm_calls"]),
                llm_prompt_tokens=int(usage["llm_prompt_tokens"]),
                llm_completion_tokens=int(usage["llm_completion_tokens"]),
                llm_unmetered_calls=int(usage["llm_unmetered_calls"]),
                llm_cost_usd=cost_by_month[month_start],
            )
        await self.session.commit()
        return RetentionPurgeRead(
            deleted_runs=len(expired),
            deleted_completed_responses=deleted_completed,
            retained_usage_months=len(usage_by_month),
        )


class WorkspaceAccessService:
    """Manage the explicit invitation and employee-roster eligibility records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = WorkspaceRepository(session)

    async def invitations(self, actor: User) -> list[InvitationRead]:
        self._require_admin(actor)
        return [_invitation_read(row) for row in await self.repo.list_invitations()]

    async def invite(self, data: InvitationCreate, actor: User) -> InvitationRead:
        self._require_admin(actor)
        existing = await self.repo.invitation_by_email(data.email)
        roster = await self.repo.roster_by_email(data.email)
        if roster is not None and roster.revoked_at is None:
            raise ConflictError("This email is already on the approved employee roster.")
        if existing is not None and existing.revoked_at is None:
            raise ConflictError("This email already has an active invitation.")

        raw_token = secrets.token_urlsafe(32)
        now = datetime.now(UTC)
        values = {
            "email": data.email,
            "display_name": data.display_name,
            "workspace_role": data.workspace_role.value,
            "function": data.function.value,
            "band": data.band.value,
            "token_digest": hashlib.sha256(raw_token.encode()).hexdigest(),
            "invited_by": actor.id,
            "expires_at": now + timedelta(days=data.expires_in_days),
            "revoked_at": None,
            "accepted_at": None,
        }
        if existing is None:
            invitation = WorkspaceInvitation(**values)
            self.repo.add_invitation(invitation)
        else:
            invitation = existing
            for field, value in values.items():
                setattr(invitation, field, value)
        self.repo.add_access_change(
            WorkspaceAccessChange(
                email=data.email,
                access_kind="invitation",
                action="invited",
                changed_by=actor.id,
                details={"role": data.workspace_role.value},
            )
        )
        await self._commit()
        result = _invitation_read(invitation)
        result.token = raw_token
        return result

    async def revoke_invitation(self, invitation_id: UUID, actor: User) -> None:
        self._require_admin(actor)
        invitation = await self.session.get(WorkspaceInvitation, invitation_id)
        if invitation is None:
            raise NotFoundError("Invitation not found.")
        if invitation.revoked_at is None:
            invitation.revoked_at = datetime.now(UTC)
            self.repo.add_access_change(
                WorkspaceAccessChange(
                    email=invitation.email,
                    access_kind="invitation",
                    action="revoked",
                    changed_by=actor.id,
                    details={},
                )
            )
            await self._commit()

    async def roster(self, actor: User) -> list[RosterRead]:
        self._require_admin(actor)
        return [_roster_read(row) for row in await self.repo.list_roster()]

    async def approve_roster(self, data: RosterCreate, actor: User) -> RosterRead:
        self._require_admin(actor)
        existing = await self.repo.roster_by_email(data.email)
        invitation = await self.repo.invitation_by_email(data.email)
        if invitation is not None and invitation.revoked_at is None:
            raise ConflictError("This email already has an active invitation.")
        if existing is not None and existing.revoked_at is None:
            raise ConflictError("This email is already approved on the roster.")

        values = {
            "email": data.email,
            "display_name": data.display_name,
            "function": data.function.value,
            "band": data.band.value,
            "approved_by": actor.id,
            "revoked_at": None,
        }
        if existing is None:
            entry = EmployeeRosterEntry(**values)
            self.repo.add_roster_entry(entry)
        else:
            entry = existing
            for field, value in values.items():
                setattr(entry, field, value)
        self.repo.add_access_change(
            WorkspaceAccessChange(
                email=data.email,
                access_kind="roster",
                action="approved",
                changed_by=actor.id,
                details={"function": data.function.value, "band": data.band.value},
            )
        )
        await self._commit()
        return _roster_read(entry)

    async def revoke_roster(self, entry_id: UUID, actor: User) -> None:
        self._require_admin(actor)
        entry = await self.session.get(EmployeeRosterEntry, entry_id)
        if entry is None:
            raise NotFoundError("Roster entry not found.")
        if entry.revoked_at is None:
            entry.revoked_at = datetime.now(UTC)
            self.repo.add_access_change(
                WorkspaceAccessChange(
                    email=entry.email,
                    access_kind="roster",
                    action="revoked",
                    changed_by=actor.id,
                    details={},
                )
            )
            await self._commit()

    async def access_history(self, actor: User, email: str | None = None) -> list[AccessChangeRead]:
        self._require_admin(actor)
        return [
            AccessChangeRead(
                id=row.id,
                email=row.email,
                access_kind=row.access_kind,
                action=row.action,
                changed_by=row.changed_by,
                changed_at=row.changed_at,
                details=row.details,
            )
            for row in await self.repo.access_history(email)
        ]

    @staticmethod
    def _require_admin(actor: User) -> None:
        if not is_workspace_admin(actor):
            raise ForbiddenError("This action requires a workspace owner or admin.")

    async def _commit(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("That email is already registered in another workspace.") from exc


def _invitation_read(row: WorkspaceInvitation) -> InvitationRead:
    return InvitationRead(
        id=row.id,
        email=row.email,
        display_name=row.display_name,
        workspace_role=WorkspaceRole(row.workspace_role),
        function=Function(row.function),
        band=Band(row.band),
        invited_by=row.invited_by,
        invited_at=row.invited_at,
        expires_at=row.expires_at,
        accepted_at=row.accepted_at,
        revoked_at=row.revoked_at,
    )


def _roster_read(row: EmployeeRosterEntry) -> RosterRead:
    return RosterRead(
        id=row.id,
        email=row.email,
        display_name=row.display_name,
        function=Function(row.function),
        band=Band(row.band),
        approved_by=row.approved_by,
        approved_at=row.approved_at,
        revoked_at=row.revoked_at,
    )
