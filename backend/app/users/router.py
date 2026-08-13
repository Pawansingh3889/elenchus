"""User routes. The list endpoint backs the dev-auth user picker.

Scaffolding for the development shim, and it should not outlive it. Under that shim a
user's id *is* their credential, so a list of every id is a list of every credential.
This route handed that out to anyone who asked, which made it the one place the
simplification stopped being a simplification and became a way in.

Two things now stand between it and a stranger. The caller must already be a known user,
which means the list can no longer be the way someone gets their first id. And
``app.main`` does not mount this router at all outside development, so in a deployment
the endpoint does not exist rather than merely being guarded.
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_201_CREATED

from app.access import is_admin_by_config
from app.auth.dependencies import get_current_user, require_admin, require_author
from app.db.session import get_session
from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import (
    AccountChangeRead,
    AccountCreate,
    AccountImpact,
    AccountRead,
    AccountUpdate,
    MeRead,
    PersonRead,
    UserRead,
)
from app.users.service import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])

# Mounted in every environment, unlike the picker above. Several routers in one module
# because they share a domain and nothing else: the first is the development auth shim
# and should not outlive it, the rest are product surfaces that have to exist in a
# deployment. Splitting them by lifetime rather than by file is the point.
directory_router = APIRouter(prefix="/api/v1/people", tags=["people"])
me_router = APIRouter(prefix="/api/v1/me", tags=["me"])
admin_router = APIRouter(prefix="/api/v1/admin/users", tags=["admin"])


@router.get("", response_model=list[UserRead])
async def list_users(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[UserRead]:
    users = await UserRepository(session).list_all()
    return [UserRead.model_validate(u) for u in users]


@directory_router.get("", response_model=list[PersonRead])
async def list_people(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_author),
) -> list[PersonRead]:
    """Everyone, with the department and groups that decide what they can be asked.

    Authors only. An author already picks a named person on the prompt and reads who
    answered by pseudonym, so the staff list tells them nothing they could not assemble;
    a respondent has no use for it and no business with it.

    It exists because reach was unexplainable without it. A survey aimed at QA reporting
    "1 of 2 answered" is correct and unreadable when nothing on any screen says who the
    two are, and one of them is an author account whose holder works on the line.
    """
    users = await UserRepository(session).list_all()
    return [PersonRead.of(u) for u in users]


@me_router.get("", response_model=MeRead)
async def read_me(user: User = Depends(get_current_user)) -> MeRead:
    """Who the caller is, and whether they may administer anything.

    Any known user, because the answer is only ever about themselves. The one field a
    client could not work out for itself is `is_admin`: half of that rule is an email
    allowlist held in server settings, and a browser deciding it locally would be a
    browser deciding it wrongly for every administrator who is not in the IT department.
    """
    return MeRead(
        id=user.id,
        display_name=user.display_name,
        role=user.role,
        department=user.department,
        is_admin=is_admin_by_config(user),
    )


@admin_router.post("", response_model=AccountRead, status_code=HTTP_201_CREATED)
async def create_account(
    data: AccountCreate,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AccountRead:
    user = await UserService(session).create_account(data, admin)
    return AccountRead.of(user)


@admin_router.put("/{user_id}", response_model=AccountRead)
async def replace_account(
    user_id: UUID,
    data: AccountUpdate,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AccountRead:
    user = await UserService(session).replace_account(user_id, data, admin)
    return AccountRead.of(user)


@admin_router.post("/{user_id}/preview", response_model=AccountImpact)
async def preview_account_change(
    user_id: UUID,
    data: AccountUpdate,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AccountImpact:
    """What this edit would change, without changing it.

    POST because it carries a body, and read-only despite the verb: nothing is written.
    The dialog calls this before saving and shows which open surveys the person would
    move in or out of, which is the moment the live-reach decision needs a witness.
    """
    return await UserService(session).preview_change(user_id, data)


@admin_router.get("/{user_id}/history", response_model=list[AccountChangeRead])
async def account_history(
    user_id: UUID,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[AccountChangeRead]:
    """Who changed this account, when, and from what to what. Append-only underneath."""
    return await UserService(session).history(user_id)
