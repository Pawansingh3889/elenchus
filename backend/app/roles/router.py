"""Admin routes for roles: define one, attach it to an account, detach it, delete it.

Every route requires an administrator, the same gate every account-shaping route in
`app.users.router` already sits behind: a role is a grant of capability, and defining
or attaching one is exactly the kind of action `require_admin` exists to guard.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.auth.dependencies import require_admin
from app.db.session import get_session
from app.roles.schemas import RoleRead, RoleWrite
from app.roles.service import RoleService
from app.users.models import User

router = APIRouter(prefix="/api/v1/admin/roles", tags=["roles"])


@router.get("", response_model=list[RoleRead])
async def list_roles(
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[RoleRead]:
    return await RoleService(session).list_roles()


@router.post("", response_model=RoleRead, status_code=HTTP_201_CREATED)
async def create_role(
    data: RoleWrite,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> RoleRead:
    return await RoleService(session).create_role(data, admin)


@router.get("/{role_id}", response_model=RoleRead)
async def get_role(
    role_id: UUID,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> RoleRead:
    return await RoleService(session).get_role(role_id)


@router.put("/{role_id}", response_model=RoleRead)
async def replace_role(
    role_id: UUID,
    data: RoleWrite,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> RoleRead:
    return await RoleService(session).replace_role(role_id, data, admin)


@router.delete("/{role_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: UUID,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    await RoleService(session).delete_role(role_id)


@router.post("/{role_id}/grant/{user_id}", response_model=RoleRead)
async def grant_role(
    role_id: UUID,
    user_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> RoleRead:
    """Attach this role to this account. Idempotent: granting a role already held
    changes nothing and still answers 200."""
    return await RoleService(session).grant(user_id, role_id, admin)


@router.delete("/{role_id}/grant/{user_id}", status_code=HTTP_204_NO_CONTENT)
async def revoke_role(
    role_id: UUID,
    user_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    await RoleService(session).revoke(user_id, role_id, admin)
