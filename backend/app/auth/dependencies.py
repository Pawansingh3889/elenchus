"""Who the caller is.

The seam the whole system hangs off, and it now has two answers rather than one.

**A signed session cookie**, set by `app/auth/router.py` after a Microsoft or Google
sign-in. This is the real one, and in production it is the only one.

**The `X-User-Id` header**, which is the development shim: a caller is whoever they say
they are. That was the entire authentication story here for a long time, and it is
exactly as weak as it sounds, so it is refused in production. It survives in dev and demo
because the test suite and local work should not need a provider, a network round trip
or a client secret, and because the seeded users have no provider accounts to sign in
with.

The order matters: the cookie is consulted first, so a browser that has genuinely signed
in cannot be overridden by a header a page happened to send.
"""

from uuid import UUID

from fastapi import Cookie, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.access import is_workspace_admin, may_author
from app.auth import oauth
from app.config import get_settings
from app.db.session import get_session
from app.errors import ForbiddenError, UnauthorizedError
from app.users.models import User, WorkspaceRole
from app.users.repository import UserRepository
from app.workspaces.repository import WorkspaceRepository


async def get_current_user(
    x_user_id: UUID | None = Header(default=None, alias="X-User-Id"),
    elenchus_session: str | None = Cookie(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    users = UserRepository(session)

    if elenchus_session:
        signed = oauth.unsign(elenchus_session)
        if signed is None:
            # Expired or tampered with. Said plainly, because the fix is to sign in
            # again and a bare 401 sends people to support instead.
            raise UnauthorizedError("Your session has expired. Please sign in again.")
        if not await WorkspaceRepository(session).resolve_identity(user_id=UUID(signed)):
            raise UnauthorizedError("That account no longer exists.")
        user = await users.get(UUID(signed))
        if user is None:
            # The account was deleted while its session was live.
            raise UnauthorizedError("That account no longer exists.")
        return user

    if x_user_id is None or get_settings().app_env == "prod":
        # No cookie and no header is nobody, and nobody is a 401.
        #
        # This branch used to substitute a hardcoded seeded id so the deployed app could
        # be clicked through without signing in. That id belonged to the account whose
        # address is also ADMIN_EMAILS, so every anonymous request arrived as an
        # administrator: /api/v1/me answered "is_admin": true to a stranger, the user
        # list handed out every id, and the admin surface answered without a credential.
        # It was added on 24 Aug 2026 by a commit about Railway migrations and CORS,
        # which is how a change to the authentication seam came to be reviewed as a
        # deployment fix.
        #
        # A caller with no credential is exactly the "missing required data" that this
        # project refuses to shrug at, so it fails loudly here instead.
        raise UnauthorizedError("Sign in to continue.")
    if not await WorkspaceRepository(session).resolve_identity(user_id=x_user_id):
        raise UnauthorizedError("Unknown user id.")
    user = await users.get(x_user_id)
    if user is None:
        raise UnauthorizedError("Unknown user id.")
    return user


async def require_author(user: User = Depends(get_current_user)) -> User:
    """The gate on the authoring surface: building, publishing, reading results.

    Derived from the job (`may_author`: manager band and up) rather than read from a
    stored role, which is the column this check used to consult and the column that
    could disagree with the org chart. The name stays `require_author` because that is
    still the question; only where the answer comes from changed.
    """
    if not may_author(user):
        raise ForbiddenError("Building surveys needs a manager-band account.")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """The gate on everything that changes who somebody is.

    Deliberately not layered on `require_author`. The two answer different questions and
    an administrator is not defined in terms of a role: `is_admin` asks the IT department
    and the email allowlist, and neither consults `role` at all. Chaining them would mean
    an administrator whose own account happened to be a respondent could no longer reach
    the screen that would fix it.
    """
    if not is_workspace_admin(user):
        raise ForbiddenError("This action requires an administrator account.")
    return user


async def require_results_reader(user: User = Depends(get_current_user)) -> User:
    """Let explicit analysts reach result routes; the service checks survey grants."""
    if user.workspace_role is not None:
        if user.workspace_role not in {
            WorkspaceRole.owner,
            WorkspaceRole.admin,
            WorkspaceRole.author,
            WorkspaceRole.analyst,
        }:
            raise ForbiddenError("This account cannot read survey results.")
        return user
    if not may_author(user):
        raise ForbiddenError("This account cannot read survey results.")
    return user
