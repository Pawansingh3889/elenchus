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

import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_201_CREATED

from app.access import is_admin_by_config, may_author
from app.auth.dependencies import get_current_user, require_admin, require_author
from app.db.session import get_session
from app.errors import NotFoundError
from app.sample_data import SAMPLE_SURVEYS
from app.seed import SEED_USERS, reset_demo
from app.templates.enums import SurveyAudience
from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import (
    AccountChangeRead,
    AccountCreate,
    AccountImpact,
    AccountRead,
    AccountUpdate,
    IdentifyRequest,
    MeRead,
    PersonRead,
    UserRead,
)
from app.users.service import UserService

logger = logging.getLogger("app.users")

router = APIRouter(prefix="/api/v1/users", tags=["users"])

# Mounted in every environment, unlike the picker above. Several routers in one module
# because they share a domain and nothing else: the first is the development auth shim
# and should not outlive it, the rest are product surfaces that have to exist in a
# deployment. Splitting them by lifetime rather than by file is the point.
directory_router = APIRouter(prefix="/api/v1/people", tags=["people"])
me_router = APIRouter(prefix="/api/v1/me", tags=["me"])
admin_router = APIRouter(prefix="/api/v1/admin/users", tags=["admin"])
# Mounted beside the picker and behind the same environment branch, because it has the
# same lifetime: both are the development shim and both go when a real login lands.
dev_router = APIRouter(prefix="/api/v1/dev", tags=["dev"])


@router.get("", response_model=list[UserRead])
async def list_users(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[UserRead]:
    users = await UserRepository(session).list_all()
    return [UserRead.of(u) for u in users]


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


@dev_router.post("/identify", response_model=UserRead)
async def identify(
    data: IdentifyRequest,
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    """Trade an address for the id that the header shim uses as a session.

    This exists because the picker above cannot bootstrap. Listing users requires a
    caller, and under this shim a caller is an id, and the only place to get an id was
    that list: a browser with empty storage could never break in, and every page's advice
    to "pick a user in the top bar" was advice about an empty dropdown.

    Be clear about what it grants, because it is not nothing. Knowing somebody's address
    is now enough to act as them. That is a smaller surface than the alternative, which
    was handing out every id at once, and it is still the whole of the authentication
    story until a real identity provider replaces `get_current_user`. It is unauthenticated
    of necessity: requiring a caller is exactly the deadlock being undone.

    So the mount is the control. ``app.main`` registers this only outside production, on
    the same branch as the picker, and an endpoint that is not registered cannot be
    reached by a bug in whatever guards it.

    An unknown address answers 404 and says so. That does leak which addresses exist, and
    it is the right trade here: a correct guess already grants far more than the knowledge
    that a guess was correct, so withholding it buys nothing and costs whoever is typing
    their own address a useful error.
    """
    email = data.email.strip().casefold()
    from app.workspaces.repository import WorkspaceRepository

    if not await WorkspaceRepository(session).resolve_identity(email=email):
        raise NotFoundError(f"No account for {email}.")
    user = await UserRepository(session).get_by_email(email)
    if user is None:
        raise NotFoundError(f"No account for {email}.")
    # Logged because this is the whole of signing in: a dev box being probed should leave
    # a trail, and "who acted as whom" is otherwise unanswerable after the fact.
    logger.info("dev identify: %s -> user=%s", email, user.id)
    return UserRead.of(user)


@directory_router.get("/reach", response_model=dict[SurveyAudience, int])
async def audience_reach(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(require_author),
) -> dict[SurveyAudience, int]:
    """How many people each audience is, right now, for the screens that aim a survey.

    The publish confirmation reads this so an author sees "4 people" beside the group
    they chose, before the choice freezes. Live like every other reach number, which is
    the recorded decision: the count follows the group as people join and leave, so the
    number shown at publish is the truth of that moment rather than a promise.

    Author-gated like the directory beside it, and never called from the respondent
    pages: break-time is a burst of respondents, and this endpoint is not on the path
    they pay for.

    `person` is absent, not zero: its reach is one by definition and the dialog already
    names the person.
    """
    return await UserService(session).reach_by_audience()


@me_router.get("", response_model=MeRead)
async def read_me(user: User = Depends(get_current_user)) -> MeRead:
    """Who the caller is, and which surfaces are theirs.

    Any known user, because the answer is only ever about themselves. Neither derived
    flag can be worked out client-side: `may_author` turns on band order, which is the
    server's fact, and half of `is_admin` is an email allowlist held in server settings,
    which a browser deciding locally would decide wrongly for every administrator who
    is not in the IT function.
    """
    return MeRead(
        id=user.id,
        display_name=user.display_name,
        function=user.function,
        band=user.band,
        may_author=may_author(user),
        is_admin=is_admin_by_config(user),
        workspace_role=user.workspace_role,
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


class ResetRead(BaseModel):
    status: str
    users: int
    surveys: int


@dev_router.post("/reset", response_model=ResetRead)
async def reset_endpoint(
    session: AsyncSession = Depends(get_session),
) -> ResetRead:
    """Wipe all data and re-seed. Demo mode only.

    Unauthenticated by necessity, like /dev/identify: the endpoint exists so a demo
    operator can restore a clean state without database access. Mounted only when
    APP_ENV=demo, which is the whole of its protection.
    """
    await reset_demo()
    logger.info("demo reset: all data wiped and re-seeded")
    return ResetRead(status="ok", users=len(SEED_USERS), surveys=len(SAMPLE_SURVEYS))
