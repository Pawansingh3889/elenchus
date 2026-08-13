"""Dev-auth dependency.

A real identity provider replaces this without touching feature code: only how
``get_current_user`` resolves the caller changes. Until then the caller identifies
via an ``X-User-Id`` header, paired with a user picker in the UI. This is an
explicit trial simplification, not a hidden fallback.
"""

from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.access import is_admin_by_config, may_author
from app.db.session import get_session
from app.errors import ForbiddenError, UnauthorizedError
from app.users.models import User
from app.users.repository import UserRepository


async def get_current_user(
    x_user_id: UUID | None = Header(default=None, alias="X-User-Id"),
    session: AsyncSession = Depends(get_session),
) -> User:
    if x_user_id is None:
        raise UnauthorizedError("Missing X-User-Id header.")
    user = await UserRepository(session).get(x_user_id)
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
