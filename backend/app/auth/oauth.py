"""Real sign-in: Microsoft and Google, over the authorization-code flow with PKCE.

What this replaces is the honest weakness of the whole system. Until now a caller was
whoever they said they were in an `X-User-Id` header, so knowing somebody's id was the
same as being them. That shim survives here for local work and the test suite, and only
outside production (see `dependencies.get_current_user`); in production the only way in
is a provider.

Two decisions worth stating, because both are the kind that look arbitrary later.

**Identity is read from the provider's userinfo endpoint, not from the id_token.** The
alternative is verifying an RS256 signature against the provider's JWKS, which means a
crypto dependency, a key cache and a rotation story. The code was exchanged for that
token over TLS against the provider's own token endpoint moments earlier, so asking the
same provider who it belongs to is the same trust with less machinery.

**An unknown address is refused, never created.** Every right in this system derives
from a job, and an account created by a first sign-in holds no job: it can be surveyed
by nobody, appears in no audience, and quietly widens every denominator it touches. So
sign-in matches an account an administrator already made, and says so plainly when it
cannot.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import secrets
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

from app.config import get_settings
from app.errors import AppError

logger = logging.getLogger("app.auth.oauth")

SESSION_COOKIE = "elenchus_session"
STATE_COOKIE = "elenchus_oauth"
# 30 days. Keeps users logged in across shifts without re-auth.
SESSION_MAX_AGE = 30 * 24 * 60 * 60
# The round trip to the provider and back. Minutes, not hours: this only has to survive
# somebody typing a password.
STATE_MAX_AGE = 10 * 60


class SignInError(AppError):
    """Sign-in failed in a way the person can read. 403 rather than 401, because the
    caller is authenticated with the provider and still not allowed in here."""

    status_code = 403
    code = "sign_in_refused"


@dataclass(frozen=True)
class Provider:
    """One identity provider, as the two endpoints and the scopes it needs.

    A dataclass rather than a class per provider: Microsoft and Google differ only in
    their URLs and in which field carries the address, and a subclass each would be two
    files to say that.
    """

    name: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    scope: str
    client_id: str
    client_secret: str

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)


def providers() -> dict[str, Provider]:
    """The providers this deployment can actually use, by name.

    Built per call from settings rather than at import, so a test can change the
    environment and see the effect, and so an unconfigured provider is simply absent
    rather than present and broken.
    """
    s = get_settings()
    tenant = s.oauth_microsoft_tenant or "common"
    return {
        "microsoft": Provider(
            name="microsoft",
            authorize_url=f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
            token_url=f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            # Graph rather than the OIDC userinfo endpoint, because it returns the
            # object id under `id`, which is what `users.microsoft_id` stores.
            userinfo_url="https://graph.microsoft.com/v1.0/me",
            scope="openid email profile User.Read",
            client_id=s.oauth_microsoft_client_id,
            client_secret=s.oauth_microsoft_client_secret,
        ),
        "google": Provider(
            name="google",
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
            scope="openid email profile",
            client_id=s.oauth_google_client_id,
            client_secret=s.oauth_google_client_secret,
        ),
    }


def enabled() -> list[str]:
    """The providers a sign-in page should offer. Empty in a deployment with none
    configured, which is the state the dev shim exists for."""
    return [name for name, p in providers().items() if p.configured]


def get_provider(name: str) -> Provider:
    provider = providers().get(name)
    if provider is None or not provider.configured:
        # Named rather than generic: the difference between "we do not support that" and
        # "somebody forgot the client secret" is the whole of the fix.
        raise SignInError(f"{name} sign-in is not configured on this deployment.")
    return provider


# --------------------------------------------------------------------------- signing


def _key() -> bytes:
    s = get_settings()
    if not s.session_secret:
        # Loudly, and only when a cookie is actually needed: a deployment that signs
        # sessions with a default would be one where anybody can mint a session.
        raise SignInError("SESSION_SECRET is not set, so sessions cannot be signed.")
    return s.session_secret.encode()


def sign(payload: str, max_age: int) -> str:
    """`payload.expiry.signature`, base64url throughout.

    Hand-rolled against the standard library rather than adding a signing dependency,
    and deliberately the smallest thing that is correct: HMAC-SHA256 over the exact
    bytes that are read back, an expiry inside the signed portion so it cannot be
    edited, and a constant-time compare on the way in.
    """
    expires = int(time.time()) + max_age
    body = f"{payload}.{expires}"
    mac = hmac.new(_key(), body.encode(), hashlib.sha256).digest()
    return f"{body}.{base64.urlsafe_b64encode(mac).decode().rstrip('=')}"


def unsign(token: str) -> str | None:
    """The payload, or None for anything that is not a live, untampered token."""
    try:
        payload, expires, signature = token.rsplit(".", 2)
    except ValueError:
        return None
    body = f"{payload}.{expires}"
    expected = (
        base64.urlsafe_b64encode(hmac.new(_key(), body.encode(), hashlib.sha256).digest())
        .decode()
        .rstrip("=")
    )
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        if int(expires) < time.time():
            return None
    except ValueError:
        return None
    return payload


# --------------------------------------------------------------------------- the flow


def authorize_url(provider: Provider, redirect_uri: str) -> tuple[str, str]:
    """Where to send the browser, and the signed state cookie that must come back.

    PKCE even though this is a confidential client with a secret: it costs one hash and
    it is what stops an intercepted code being redeemed by anyone else.
    """
    verifier = secrets.token_urlsafe(48)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    )
    nonce = secrets.token_urlsafe(16)
    query = urlencode(
        {
            "client_id": provider.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": provider.scope,
            "state": nonce,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            # Microsoft returns a refresh token without this and Google needs it for
            # consent; neither is stored, because a session here is short and re-auth is
            # a redirect rather than a problem.
            "prompt": "select_account",
        }
    )
    # The verifier travels in the cookie rather than in a server-side store, so this
    # scales across processes and survives a restart mid-sign-in.
    state = sign(f"{provider.name}:{nonce}:{verifier}", STATE_MAX_AGE)
    return f"{provider.authorize_url}?{query}", state


async def exchange(
    provider: Provider, code: str, verifier: str, redirect_uri: str
) -> dict[str, Any]:
    """Code for tokens, then tokens for who this is. Returns the provider's own profile."""
    async with httpx.AsyncClient(timeout=20) as client:
        token_response = await client.post(
            provider.token_url,
            data={
                "client_id": provider.client_id,
                "client_secret": provider.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                "code_verifier": verifier,
            },
            headers={"Accept": "application/json"},
        )
        if token_response.status_code != 200:
            logger.warning(
                "token exchange failed: provider=%s status=%s body=%s",
                provider.name,
                token_response.status_code,
                token_response.text[:300],
            )
            raise SignInError("The provider would not complete the sign-in. Please try again.")
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise SignInError("The provider returned no access token.")

        profile = await client.get(
            provider.userinfo_url, headers={"Authorization": f"Bearer {access_token}"}
        )
        if profile.status_code != 200:
            raise SignInError("The provider would not say who you are.")
        return dict(profile.json())


def identity_of(provider: Provider, profile: dict[str, Any]) -> tuple[str, str | None]:
    """(email, provider subject) from whichever fields this provider uses.

    Microsoft Graph puts a work address in `mail` and leaves it null for accounts that
    have only a UPN, which is why the fallback exists rather than being defensive
    padding. The subject is the Entra object id, and it is what gets written to
    `users.microsoft_id` on a first sign-in so the link survives an address change.
    """
    if provider.name == "microsoft":
        email = profile.get("mail") or profile.get("userPrincipalName") or ""
        return str(email).strip().casefold(), profile.get("id")
    email = profile.get("email") or ""
    if not profile.get("email_verified", True):
        # An unverified address on a provider that reports it is somebody else's account
        # waiting to happen, since this system matches people by address.
        raise SignInError("That account's email address is not verified with the provider.")
    return str(email).strip().casefold(), profile.get("sub")
