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

from app.auth.dependencies import get_current_user, require_author
from app.db.session import get_session
from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import PersonRead, UserRead

router = APIRouter(prefix="/api/v1/users", tags=["users"])

# Mounted in every environment, unlike the picker above. Two routers in one module
# because they share a domain and nothing else: one is the development auth shim and
# should not outlive it, the other is a page authors use.
directory_router = APIRouter(prefix="/api/v1/people", tags=["people"])


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
