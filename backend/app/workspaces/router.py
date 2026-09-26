"""Workspace settings and retention maintenance routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.auth.dependencies import get_current_user, require_admin
from app.db.session import get_session
from app.users.models import User
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
from app.workspaces.service import WorkspaceAccessService, WorkspaceService

router = APIRouter(prefix="/api/v1/workspace", tags=["workspace"])


@router.get("/retention", response_model=RetentionRead)
async def read_retention(
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> RetentionRead:
    return await WorkspaceService(session).retention()


@router.put("/retention", response_model=RetentionRead)
async def update_retention(
    data: RetentionUpdate,
    owner: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> RetentionRead:
    return await WorkspaceService(session).update_retention(data, owner)


@router.post("/retention/purge", response_model=RetentionPurgeRead)
async def purge_retention(
    limit: int = Query(default=100, ge=1, le=1000),
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> RetentionPurgeRead:
    return await WorkspaceService(session).purge_expired(admin, limit=limit)


@router.get("/invitations", response_model=list[InvitationRead])
async def list_invitations(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[InvitationRead]:
    return await WorkspaceAccessService(session).invitations(admin)


@router.post("/invitations", response_model=InvitationRead, status_code=HTTP_201_CREATED)
async def create_invitation(
    data: InvitationCreate,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> InvitationRead:
    return await WorkspaceAccessService(session).invite(data, admin)


@router.delete("/invitations/{invitation_id}", status_code=HTTP_204_NO_CONTENT)
async def revoke_invitation(
    invitation_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    await WorkspaceAccessService(session).revoke_invitation(invitation_id, admin)


@router.get("/roster", response_model=list[RosterRead])
async def list_roster(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[RosterRead]:
    return await WorkspaceAccessService(session).roster(admin)


@router.post("/roster", response_model=RosterRead, status_code=HTTP_201_CREATED)
async def approve_roster(
    data: RosterCreate,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> RosterRead:
    return await WorkspaceAccessService(session).approve_roster(data, admin)


@router.delete("/roster/{entry_id}", status_code=HTTP_204_NO_CONTENT)
async def revoke_roster(
    entry_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    await WorkspaceAccessService(session).revoke_roster(entry_id, admin)


@router.get("/access-history", response_model=list[AccessChangeRead])
async def access_history(
    email: str | None = None,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[AccessChangeRead]:
    return await WorkspaceAccessService(session).access_history(admin, email)
