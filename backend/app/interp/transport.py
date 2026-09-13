"""The one module that talks to the interpretability service over HTTP.

Every way that service can fail becomes a typed error here: switched off (503), not
reachable or refusing the token (502), or refusing the prompt itself (422).
"""

from typing import Any

import httpx

from app.config import get_settings
from app.errors import AppError, ValidationError

CONNECT_SECONDS = 5.0


class InterpNotConfiguredError(AppError):
    """Asked for an analysis on a deployment that has not switched the service on."""

    status_code = 503
    code = "interp_not_configured"


class InterpUnavailableError(AppError):
    """The service is configured but cannot be reached, or answered wrongly."""

    status_code = 502
    code = "interp_unavailable"


class InterpTransport:
    def __init__(
        self,
        base_url: str,
        token: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        # Connecting fails fast: a service that is not running should say so in seconds,
        # while reading is allowed the full timeout, because a CPU reads a long prompt slowly.
        self._timeout = httpx.Timeout(timeout_seconds, connect=CONNECT_SECONDS)
        self._transport = transport

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                return await client.request(method, f"{self._base_url}{path}", **kwargs)
        except httpx.HTTPError as exc:
            raise InterpUnavailableError(
                f"The interpretability service at {self._base_url} could not be reached "
                f"({type(exc).__name__}). Start it with `make interp`."
            ) from exc

    async def health(self) -> dict[str, Any]:
        response = await self._request("GET", "/health")
        if response.status_code != 200:
            raise InterpUnavailableError(
                f"The interpretability service answered {response.status_code} to a health check."
            )
        body: dict[str, Any] = response.json()
        return body

    async def analyse(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._post("/analyse", payload)

    async def attribute(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._post("/attribute", payload)

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self._request(
            "POST", path, json=payload, headers={"Authorization": f"Bearer {self._token}"}
        )
        if response.status_code == 401:
            raise InterpUnavailableError(
                "The interpretability service refused the token: INTERP_TOKEN differs between "
                "the backend and the service."
            )
        if response.status_code in (413, 422):
            raise ValidationError(
                f"The interpretability service refused this prompt: {_detail(response)}"
            )
        if response.status_code != 200:
            raise InterpUnavailableError(
                f"The interpretability service answered {response.status_code}: "
                f"{_detail(response)}"
            )
        body: dict[str, Any] = response.json()
        return body


def _detail(response: httpx.Response) -> str:
    try:
        return str(response.json()["detail"])[:300]
    except (ValueError, KeyError, TypeError):
        return response.text[:300]


def get_transport() -> InterpTransport:
    settings = get_settings()
    if not settings.interp_enabled:
        raise InterpNotConfiguredError(
            "The interpretability service is not enabled on this deployment: set "
            "INTERP_ENABLED, INTERP_BASE_URL and INTERP_TOKEN, and start it with `make interp`."
        )
    return InterpTransport(
        settings.interp_base_url, settings.interp_token, settings.interp_timeout_seconds
    )
