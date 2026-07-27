"""The LLM client is the only place the Anthropic SDK is touched, so it is also the
only place SDK failures may be turned into something the API can render.
"""

from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from anthropic import APIConnectionError, APIStatusError
from anthropic.types import TextBlock, ToolUseBlock

from app.llm.client import (
    LLMClient,
    LLMError,
    NoToolCallError,
    TruncatedTurnError,
    _api_errors,
)

_REQUEST = httpx.Request("POST", "https://api.anthropic.com/v1/messages")


def _client_returning(content: list[Any], stop_reason: str = "tool_use"):
    """An LLMClient wired to a canned SDK response, with the captured request kwargs.

    Built without __init__ so no API key is needed — the SDK boundary is the only thing
    under test here.
    """
    client = object.__new__(LLMClient)
    client._model = "test-model"
    sent: dict[str, Any] = {}

    async def create(**kwargs: Any) -> Any:
        sent.update(kwargs)
        return SimpleNamespace(content=content, usage=None, stop_reason=stop_reason)

    client._client = SimpleNamespace(messages=SimpleNamespace(create=create))
    return client, sent


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


async def test_a_turn_yields_one_tool_even_if_the_model_sends_two():
    """Parallel tool use is on by default. A turn carrying record_answer *and* move_on
    used to hand the engine the last block, discarding an answer the respondent gave
    and advancing anyway. The request now forbids it, and the first tool wins if a
    model ignores that."""
    client, sent = _client_returning(
        [
            TextBlock(type="text", text="Got it."),
            ToolUseBlock(type="tool_use", id="a", name="record_answer", input={"value": "Lead"}),
            ToolUseBlock(type="tool_use", id="b", name="move_on", input={}),
        ]
    )

    turn = await client.tool_turn(system="s", messages=[{"role": "user", "content": "x"}], tools=[])

    assert turn.tool_name == "record_answer"
    assert turn.tool_input == {"value": "Lead"}
    assert turn.text == "Got it."
    assert sent["tool_choice"]["disable_parallel_tool_use"] is True


async def test_a_truncated_turn_is_named_rather_than_read_as_chatter():
    """max_tokens with no tool block is not a chatty model: retrying it at the same
    budget truncates identically, so it must not raise the retryable error."""
    client, _ = _client_returning([TextBlock(type="text", text="Let me")], stop_reason="max_tokens")

    with pytest.raises(TruncatedTurnError, match="token limit"):
        await client.tool_turn(system="s", messages=[{"role": "user", "content": "x"}], tools=[])


async def test_a_genuinely_chatty_turn_stays_retryable():
    client, _ = _client_returning([TextBlock(type="text", text="Sure!")], stop_reason="end_turn")

    with pytest.raises(NoToolCallError):
        await client.tool_turn(system="s", messages=[{"role": "user", "content": "x"}], tools=[])


async def test_one_shot_tool_call_also_forbids_parallel_tools():
    client, sent = _client_returning(
        [ToolUseBlock(type="tool_use", id="a", name="generate", input={"title": "T"})]
    )

    result = await client.tool_call(
        system="s", prompt="p", tool_name="generate", tool_description="d", input_schema={}
    )

    assert result == {"title": "T"}
    assert sent["tool_choice"]["disable_parallel_tool_use"] is True
