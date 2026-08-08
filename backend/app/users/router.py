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

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_session
from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import UserRead

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("", response_model=list[UserRead])
async def list_users(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[UserRead]:
    users = await UserRepository(session).list_all()
    return [UserRead.model_validate(u) for u in users]
