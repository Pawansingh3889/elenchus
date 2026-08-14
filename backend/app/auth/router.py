"""The sign-in routes: start with a provider, come back with a session.

Thin on purpose, in the way every router here is thin: parse, call one thing, shape the
response. What is worth reading is `oauth.py`, which holds the decisions.
"""

import logging

from fastapi import APIRouter, Cookie, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import oauth
from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.db.session import get_session
from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import UserRead

logger = logging.getLogger("app.auth")

# The full path, as every other router here spells it: this app mounts routers without
# a global prefix, so a bare "/auth" lands the routes one level up from every other
# endpoint and 404s for anything calling the versioned API.
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _redirect_uri(provider: str) -> str:
    return f"{get_settings().public_base_url.rstrip('/')}/api/v1/auth/{provider}/callback"


@router.get("/providers")
async def sign_in_options() -> dict[str, list[str]]:
    """Which providers this deployment can offer, so the page draws only real buttons.

    Unauthenticated of necessity, like the dev picker, and unlike it this leaks nothing:
    the answer is which of two well-known products the deployment is wired to.
    """
    return {"providers": oauth.enabled()}


@router.get("/{provider}/login")
async def login(provider: str) -> RedirectResponse:
    """Send the browser to the provider, remembering the round trip in a signed cookie."""
    p = oauth.get_provider(provider)
    url, state = oauth.authorize_url(p, _redirect_uri(provider))
    response = RedirectResponse(url, status_code=307)
    response.set_cookie(
        oauth.STATE_COOKIE,
        state,
        max_age=oauth.STATE_MAX_AGE,
        httponly=True,
        secure=get_settings().app_env == "prod",
        # Lax rather than Strict: the provider redirects the browser back here, and a
        # Strict cookie is not sent on that navigation, which breaks the callback.
        samesite="lax",
        path="/",
    )
    return response


@router.get("/{provider}/callback")
async def callback(
    provider: str,
    code: str | None = None,
    state: str | None = None,
    session: AsyncSession = Depends(get_session),
    elenchus_oauth: str | None = Cookie(default=None),
) -> RedirectResponse:
    """Finish the round trip: verify the state, exchange the code, find the account.

    Every refusal below lands the browser back on the app with a readable reason in the
    query string rather than showing a JSON error page: the person who cannot get in is
    a shift manager, not a developer.
    """
    settings = get_settings()
    front = settings.frontend_origin.rstrip("/")

    def refuse(reason: str) -> RedirectResponse:
        logger.info("sign-in refused: provider=%s reason=%s", provider, reason)
        return RedirectResponse(f"{front}/?sign_in_error={reason}", status_code=307)

    p = oauth.get_provider(provider)
    if not code or not state:
        return refuse("no_code")
    signed = oauth.unsign(elenchus_oauth or "")
    if signed is None:
        return refuse("expired")
    want_provider, nonce, verifier = signed.split(":", 2)
    # The state has to match the cookie this browser was given, and the cookie has to
    # belong to the provider being called back: without the second check a code from one
    # provider could be redeemed against the other's callback.
    if want_provider != provider or nonce != state:
        return refuse("state_mismatch")

    profile = await oauth.exchange(p, code, verifier, _redirect_uri(provider))
    email, subject = oauth.identity_of(p, profile)
    if not email:
        return refuse("no_email")

    users = UserRepository(session)
    user = await users.get_by_email(email)
    if user is None:
        # The decision this system rests on: an account is made by an administrator, who
        # gives it a job, and every right derives from that job. A sign-in cannot invent
        # one.
        return refuse("no_account")

    # Link the provider's stable id on first use, so a later address change does not
    # orphan the account. Only ever filled in, never overwritten: two different subjects
    # on one address is a conflict a person should look at, not something to silently
    # resolve.
    if provider == "microsoft" and subject and not user.microsoft_id:
        user.microsoft_id = subject
        await session.commit()

    response = RedirectResponse(front, status_code=307)
    response.set_cookie(
        oauth.SESSION_COOKIE,
        oauth.sign(str(user.id), oauth.SESSION_MAX_AGE),
        max_age=oauth.SESSION_MAX_AGE,
        httponly=True,
        secure=settings.app_env == "prod",
        samesite="lax",
        path="/",
    )
    response.delete_cookie(oauth.STATE_COOKIE, path="/")
    logger.info("signed in: user=%s provider=%s", user.id, provider)
    return response


@router.post("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse(get_settings().frontend_origin.rstrip("/"), status_code=303)
    response.delete_cookie(oauth.SESSION_COOKIE, path="/")
    return response


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)) -> User:
    """Who the caller is, however they got here.

    The browser needs this after a callback, because the session arrives as an HttpOnly
    cookie it cannot read. It answers the same for a dev-shim caller, so the frontend has
    one way to ask rather than one per sign-in method.
    """
    return user
