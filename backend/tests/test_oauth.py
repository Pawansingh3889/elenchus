"""Real sign-in, at the boundary: what a session admits and what it refuses.

The provider itself is never called here. What is worth pinning is everything on this
side of it: that a session cookie is unforgeable, that the shim dies in production, and
that an address nobody made an account for is turned away rather than quietly given one.
"""

import time
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.auth import oauth
from app.auth.dependencies import get_current_user
from app.auth.router import callback
from app.config import Settings, get_settings
from app.errors import UnauthorizedError


@pytest.fixture(autouse=True)
def _secret(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "test-secret-not-a-real-one")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_a_signed_value_comes_back_unchanged():
    token = oauth.sign("hello", 60)
    assert oauth.unsign(token) == "hello"


@pytest.mark.parametrize("environment", ["production", "staging", "demo", ""])
def test_misspelled_environment_cannot_enable_development_auth(monkeypatch, environment):
    monkeypatch.setenv("APP_ENV", environment)
    with pytest.raises(ValidationError, match="app_env"):
        Settings(_env_file=None)


def test_a_tampered_payload_is_refused():
    token = oauth.sign(str(uuid4()), 60)
    payload, expires, signature = token.rsplit(".", 2)
    forged = f"{uuid4()}.{expires}.{signature}"
    assert oauth.unsign(forged) is None


def test_an_extended_expiry_is_refused():
    """The expiry is inside the signed body, so moving it invalidates the signature.
    Without that, a cookie would be valid forever to anyone who could edit it."""
    token = oauth.sign("someone", 60)
    payload, expires, signature = token.rsplit(".", 2)
    assert oauth.unsign(f"{payload}.{int(expires) + 100000}.{signature}") is None


def test_an_expired_token_is_refused():
    token = oauth.sign("someone", -1)
    assert oauth.unsign(token) is None


def test_a_token_signed_with_another_key_is_refused(monkeypatch):
    token = oauth.sign("someone", 60)
    monkeypatch.setenv("SESSION_SECRET", "a-different-deployment")
    get_settings.cache_clear()
    assert oauth.unsign(token) is None


def test_junk_is_refused_rather_than_raising():
    for junk in ("", "x", "a.b", "....", "not.a.token"):
        assert oauth.unsign(junk) is None


def test_an_unconfigured_provider_says_so(monkeypatch):
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "")
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "")
    get_settings.cache_clear()
    assert "google" not in oauth.enabled()
    with pytest.raises(oauth.SignInError):
        oauth.get_provider("google")


def test_a_configured_provider_is_offered(monkeypatch):
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "id")
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "secret")
    get_settings.cache_clear()
    assert "google" in oauth.enabled()


def test_the_authorize_url_carries_pkce_and_matching_state(monkeypatch):
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "id")
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "secret")
    get_settings.cache_clear()
    url, state = oauth.authorize_url(oauth.get_provider("google"), "http://x/cb")
    assert "code_challenge=" in url and "code_challenge_method=S256" in url
    provider, nonce, verifier = oauth.unsign(state).split(":", 2)
    assert provider == "google"
    # The nonce in the cookie is the state the provider will echo back, and the verifier
    # is what proves this browser started the flow.
    assert f"state={nonce}" in url
    assert len(verifier) > 32


def test_microsoft_falls_back_to_the_principal_name():
    """Graph leaves `mail` null on accounts that only have a UPN, which is common in a
    directory where not everyone has a mailbox."""
    provider = oauth.providers()["microsoft"]
    email, subject = oauth.identity_of(
        provider, {"mail": None, "userPrincipalName": "Ava@Plant.local", "id": "oid-1"}
    )
    assert (email, subject) == ("ava@plant.local", "oid-1")


def test_google_refuses_an_unverified_address():
    provider = oauth.providers()["google"]
    with pytest.raises(oauth.SignInError):
        oauth.identity_of(provider, {"email": "someone@gmail.com", "email_verified": False})


@pytest.mark.parametrize(
    "claim", [{}, {"email_verified": None}, {"email_verified": "false"}, {"email_verified": 1}]
)
def test_google_needs_explicit_email_verification(claim):
    provider = oauth.providers()["google"]
    with pytest.raises(oauth.SignInError):
        oauth.identity_of(provider, {"email": "someone@example.com", **claim})


async def test_production_refuses_a_known_user_id_without_a_session(session, author, monkeypatch):
    """Knowing an account id must not let a stranger sign in as that account."""
    monkeypatch.setenv("APP_ENV", "prod")
    get_settings.cache_clear()
    with pytest.raises(UnauthorizedError):
        await get_current_user(x_user_id=author.id, elenchus_session=None, session=session)


async def test_development_keeps_the_header_shim(session, author, monkeypatch):
    monkeypatch.setenv("APP_ENV", "dev")
    get_settings.cache_clear()
    user = await get_current_user(x_user_id=author.id, elenchus_session=None, session=session)
    assert user.id == author.id


async def test_a_session_cookie_signs_the_caller_in(session, author, monkeypatch):
    """The cookie replaces the header entirely: no id is passed here at all, and it works
    in production, where the header does not."""
    monkeypatch.setenv("APP_ENV", "prod")
    get_settings.cache_clear()
    cookie = oauth.sign(str(author.id), 60)
    user = await get_current_user(x_user_id=None, elenchus_session=cookie, session=session)
    assert user.id == author.id


async def test_a_forged_session_cookie_is_refused(session, author):
    forged = f"{author.id}.{int(time.time()) + 999}.nonsense"
    with pytest.raises(UnauthorizedError):
        await get_current_user(x_user_id=None, elenchus_session=forged, session=session)


async def test_the_cookie_wins_over_the_header(session, author, other_author):
    """A browser that genuinely signed in cannot be re-identified by a header a page
    happened to send."""
    cookie = oauth.sign(str(author.id), 60)
    user = await get_current_user(
        x_user_id=other_author.id, elenchus_session=cookie, session=session
    )
    assert user.id == author.id


async def test_the_callback_refuses_an_address_with_no_account(session, monkeypatch):
    """The decision the whole access model rests on: every right derives from a job, and
    a sign-in cannot invent one. An unknown address is sent back with a reason rather
    than silently becoming a jobless account."""
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "id")
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "secret")
    get_settings.cache_clear()

    async def fake_exchange(*_args, **_kwargs):
        return {"email": "stranger@example.com", "email_verified": True, "sub": "g-1"}

    monkeypatch.setattr(oauth, "exchange", fake_exchange)
    _url, state = oauth.authorize_url(oauth.get_provider("google"), "http://x/cb")
    nonce = oauth.unsign(state).split(":", 2)[1]
    response = await callback(
        provider="google", code="abc", state=nonce, session=session, elenchus_oauth=state
    )
    assert "sign_in_error=no_account" in response.headers["location"]


async def test_the_callback_signs_in_an_account_that_exists(session, author, monkeypatch):
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "id")
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "secret")
    get_settings.cache_clear()

    async def fake_exchange(*_args, **_kwargs):
        return {"email": author.email.upper(), "email_verified": True, "sub": "g-1"}

    monkeypatch.setattr(oauth, "exchange", fake_exchange)
    _url, state = oauth.authorize_url(oauth.get_provider("google"), "http://x/cb")
    nonce = oauth.unsign(state).split(":", 2)[1]
    response = await callback(
        provider="google", code="abc", state=nonce, session=session, elenchus_oauth=state
    )
    # Case-folded on the way in, because one address is one account and the provider
    # decides the casing.
    assert "sign_in_error" not in response.headers["location"]
    assert oauth.SESSION_COOKIE in response.headers["set-cookie"]


async def test_the_callback_refuses_a_mismatched_state(session, monkeypatch):
    """Without this, a code obtained elsewhere could be redeemed against this callback."""
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "id")
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "secret")
    get_settings.cache_clear()
    _url, state = oauth.authorize_url(oauth.get_provider("google"), "http://x/cb")
    response = await callback(
        provider="google",
        code="abc",
        state="not-the-nonce",
        session=session,
        elenchus_oauth=state,
    )
    assert "sign_in_error=state_mismatch" in response.headers["location"]


@pytest.mark.parametrize("stored_id", [None, "different-subject"])
async def test_a_microsoft_mail_address_cannot_claim_an_account(
    session, author, monkeypatch, stored_id
):
    monkeypatch.setenv("OAUTH_MICROSOFT_CLIENT_ID", "id")
    monkeypatch.setenv("OAUTH_MICROSOFT_CLIENT_SECRET", "secret")
    get_settings.cache_clear()
    author.microsoft_id = stored_id
    await session.commit()

    async def fake_exchange(*_args, **_kwargs):
        return {"mail": author.email, "id": "entra-oid-42"}

    monkeypatch.setattr(oauth, "exchange", fake_exchange)
    _url, state = oauth.authorize_url(oauth.get_provider("microsoft"), "http://x/cb")
    nonce = oauth.unsign(state).split(":", 2)[1]
    response = await callback(
        provider="microsoft", code="abc", state=nonce, session=session, elenchus_oauth=state
    )
    await session.refresh(author)
    assert author.microsoft_id == stored_id
    assert "sign_in_error=no_account" in response.headers["location"]
    assert "set-cookie" not in response.headers


async def test_linked_microsoft_subject_survives_a_changed_email(session, author, monkeypatch):
    monkeypatch.setenv("OAUTH_MICROSOFT_CLIENT_ID", "id")
    monkeypatch.setenv("OAUTH_MICROSOFT_CLIENT_SECRET", "secret")
    get_settings.cache_clear()
    author.microsoft_id = "entra-linked-subject"
    await session.commit()

    async def fake_exchange(*_args, **_kwargs):
        return {"mail": "changed@example.test", "id": "entra-linked-subject"}

    monkeypatch.setattr(oauth, "exchange", fake_exchange)
    _url, state = oauth.authorize_url(oauth.get_provider("microsoft"), "http://x/cb")
    nonce = oauth.unsign(state).split(":", 2)[1]
    response = await callback(
        provider="microsoft", code="abc", state=nonce, session=session, elenchus_oauth=state
    )
    assert "sign_in_error" not in response.headers["location"]
    assert oauth.SESSION_COOKIE in response.headers["set-cookie"]


def test_the_sign_in_routes_are_mounted_where_the_browser_looks():
    """The tests above call the callback directly, so none of them would notice the
    router being mounted on the wrong path. This one did, when it was: the prefix said
    `/auth` while every other router in this app spells the version out, so the browser
    asked `/api/v1/auth/providers` and got a 404 while the suite stayed green.

    Read off the router rather than the app, matching the user-list tests beside it, and
    because FastAPI does not flatten included routers into `app.routes`.
    """
    from app.auth.router import router

    paths = {getattr(r, "path", "") for r in router.routes}
    assert paths == {
        "/api/v1/auth/providers",
        "/api/v1/auth/{provider}/login",
        "/api/v1/auth/{provider}/callback",
        "/api/v1/auth/logout",
        "/api/v1/auth/me",
    }


@pytest.mark.parametrize("environment,offered", [("dev", True), ("prod", False)])
async def test_address_sign_in_is_offered_only_where_it_is_mounted(
    monkeypatch, environment, offered
):
    """Production has no /dev/identify, so its top bar must not draw the box that calls it."""
    from app.auth.router import sign_in_options

    monkeypatch.setenv("APP_ENV", environment)
    get_settings.cache_clear()
    assert (await sign_in_options()).address_sign_in is offered
