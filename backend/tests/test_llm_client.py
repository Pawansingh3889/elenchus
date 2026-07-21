"""The LLM client is the only place the Anthropic SDK is touched, so it is also the
only place SDK failures may be turned into something the API can render.
"""

import httpx
import pytest
from anthropic import APIConnectionError, APIStatusError

from app.llm.client import LLMError, _api_errors

_REQUEST = httpx.Request("POST", "https://api.anthropic.com/v1/messages")


async def test_transport_failure_becomes_a_typed_error():
    with pytest.raises(LLMError, match="Could not reach"):
        async with _api_errors():
            raise APIConnectionError(request=_REQUEST)


async def test_status_error_carries_the_upstream_reason():
    body = {"error": {"type": "invalid_request_error", "message": "credit balance is too low"}}
    response = httpx.Response(400, request=_REQUEST, json=body)
    with pytest.raises(LLMError, match="credit balance is too low") as caught:
        async with _api_errors():
            raise APIStatusError("bad request", response=response, body=body)
    assert caught.value.status_code == 502  # ours failed because theirs did


async def test_status_error_without_a_body_still_reports_something():
    response = httpx.Response(500, request=_REQUEST, text="upstream exploded")
    with pytest.raises(LLMError, match="500"):
        async with _api_errors():
            raise APIStatusError("server error", response=response, body=None)
