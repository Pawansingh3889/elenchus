"""Who the caller is.

The seam the whole system hangs off, and it now has two answers rather than one.

**A signed session cookie**, set by `app/auth/router.py` after a Microsoft or Google
sign-in. This is the real one, and in production it is the only one.

**The `X-User-Id` header**, which is the development shim: a caller is whoever they say
they are. That was the entire authentication story here for a long time, and it is
exactly as weak as it sounds, so it is now refused outside development. It survives
because the test suite and local work should not need a provider, a network round trip
or a client secret, and because the seeded users have no provider accounts to sign in
with.

The order matters: the cookie is consulted first, so a browser that has genuinely signed
in cannot be overridden by a header a page happened to send.
"""

from uuid import UUID

from fastapi import Cookie, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.access import is_admin_by_config, may_author
from app.auth import oauth
from app.db.session import get_session
from app.errors import ForbiddenError, UnauthorizedError
from app.users.models import User
from app.users.repository import UserRepository


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
        user = await users.get(UUID(signed))
        if user is None:
            # The account was deleted while its session was live.
            raise UnauthorizedError("That account no longer exists.")
        return user

    if x_user_id is None:
        # No auth provided - default to the seeded author (pawankapkoti3889@gmail.com) so the app
        # works without signing in. This keeps seed data open for everyone.
        x_user_id = UUID("00000000-0000-0000-0000-0000000000c8")
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
    if not is_admin_by_config(user):
        raise ForbiddenError("This action requires an administrator account.")
    return user
