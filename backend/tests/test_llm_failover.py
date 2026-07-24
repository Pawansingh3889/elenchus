"""Backup-provider tests: the failover wrapper and the OpenAI-compatible client.

All offline — the OpenAI-compatible client is driven through an httpx MockTransport, so no
network or API key is touched, and the failover wrapper uses in-memory doubles.
"""

import json
from typing import Any

import httpx
import pytest

from app.llm.backup import OpenAICompatibleLLMClient
from app.llm.client import LLMError, ToolTurn
from app.llm.failover import FailoverLLM

# ---------------------------------------------------------------- failover wrapper


class _StubLLM:
    """Records that it was called; either returns scripted values or raises LLMError."""

    def __init__(
        self,
        *,
        turn: ToolTurn | None = None,
        payload: dict[str, Any] | None = None,
        fail: bool = False,
    ) -> None:
        self._turn = turn
        self._payload = payload
        self._fail = fail
        self.tool_call_calls = 0
        self.tool_turn_calls = 0

    async def tool_call(self, **_: Any) -> dict[str, Any]:
        self.tool_call_calls += 1
        if self._fail:
            raise LLMError("primary down")
        assert self._payload is not None
        return self._payload

    async def tool_turn(self, **_: Any) -> ToolTurn:
        self.tool_turn_calls += 1
        if self._fail:
            raise LLMError("primary down")
        assert self._turn is not None
        return self._turn


_ARGS: dict[str, Any] = dict(
    system="s", prompt="p", tool_name="t", tool_description="d", input_schema={}, max_tokens=16
)
_TURN_ARGS: dict[str, Any] = dict(system="s", messages=[], tools=[], max_tokens=16)


async def test_failover_prefers_primary_and_never_touches_backup():
    primary = _StubLLM(payload={"ok": True}, turn=ToolTurn("hi", "move_on", {}))
    backup = _StubLLM(payload={"ok": False}, turn=ToolTurn("no", "move_on", {}))
    failover = FailoverLLM(primary, backup)

    assert await failover.tool_call(**_ARGS) == {"ok": True}
    assert await failover.tool_turn(**_TURN_ARGS) == ToolTurn("hi", "move_on", {})
    assert (backup.tool_call_calls, backup.tool_turn_calls) == (0, 0)


async def test_failover_uses_backup_when_primary_fails():
    primary = _StubLLM(fail=True)
    backup = _StubLLM(payload={"from": "backup"}, turn=ToolTurn("hey", "record_answer", {"v": 1}))
    failover = FailoverLLM(primary, backup)

    assert await failover.tool_call(**_ARGS) == {"from": "backup"}
    assert await failover.tool_turn(**_TURN_ARGS) == ToolTurn("hey", "record_answer", {"v": 1})
    assert (primary.tool_call_calls, primary.tool_turn_calls) == (1, 1)
    assert (backup.tool_call_calls, backup.tool_turn_calls) == (1, 1)


async def test_failover_propagates_backup_failure_loudly():
    failover = FailoverLLM(_StubLLM(fail=True), _StubLLM(fail=True))
    with pytest.raises(LLMError):
        await failover.tool_call(**_ARGS)


# ---------------------------------------------------------------- OpenAI-compatible client


def _client(handler: Any) -> OpenAICompatibleLLMClient:
    return OpenAICompatibleLLMClient(
        base_url="http://backup.local/v1",
        api_key="k",
        model="nemotron-test",
        transport=httpx.MockTransport(handler),
    )


def _tool_response(name: str, arguments: dict[str, Any], text: str = "") -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "choices": [
                {
                    "message": {
                        "content": text,
                        "tool_calls": [
                            {"function": {"name": name, "arguments": json.dumps(arguments)}}
                        ],
                    }
                }
            ]
        },
    )


async def test_tool_call_forces_the_named_tool_and_parses_arguments():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        seen["auth"] = request.headers.get("Authorization")
        return _tool_response("draft_survey_template", {"title": "Onboarding"})

    result = await _client(handler).tool_call(
        system="draft it",
        prompt="an onboarding survey",
        tool_name="draft_survey_template",
        tool_description="Return a template.",
        input_schema={"type": "object"},
        max_tokens=64,
    )

    assert result == {"title": "Onboarding"}
    assert seen["auth"] == "Bearer k"
    # The request forced exactly the tool we asked for.
    assert seen["body"]["tool_choice"] == {
        "type": "function",
        "function": {"name": "draft_survey_template"},
    }
    assert seen["body"]["tools"][0]["function"]["name"] == "draft_survey_template"


async def test_tool_turn_requires_a_tool_and_returns_text_plus_choice():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return _tool_response("record_answer", {"value": "Line lead"}, text="Thanks.")

    turn = await _client(handler).tool_turn(
        system="conduct",
        messages=[{"role": "user", "content": "line lead"}],
        tools=[
            {"name": "record_answer", "description": "save", "input_schema": {"type": "object"}}
        ],
    )

    assert turn == ToolTurn(
        text="Thanks.", tool_name="record_answer", tool_input={"value": "Line lead"}
    )
    assert seen["body"]["tool_choice"] == "required"


async def test_missing_tool_call_fails_loudly():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "hi"}}]})

    with pytest.raises(LLMError, match="no tool call"):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])


async def test_tool_call_written_into_content_is_salvaged():
    """Local models often put the tool-call JSON in the text instead of tool_calls."""

    def handler(_: httpx.Request) -> httpx.Response:
        content = json.dumps({"name": "record_answer", "arguments": {"value": 4}})
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    turn = await _client(handler).tool_turn(system="s", messages=[], tools=[])
    assert turn == ToolTurn(text="", tool_name="record_answer", tool_input={"value": 4})


async def test_prose_content_is_not_mistaken_for_a_tool_call():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"choices": [{"message": {"content": 'I would call {"name"} here'}}]}
        )

    with pytest.raises(LLMError, match="no tool call"):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])


async def test_http_error_becomes_a_typed_error():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="upstream unavailable")

    with pytest.raises(LLMError, match="503"):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])


async def test_wrong_tool_name_on_forced_call_is_rejected():
    def handler(_: httpx.Request) -> httpx.Response:
        return _tool_response("some_other_tool", {"x": 1})

    with pytest.raises(LLMError, match="expected"):
        await _client(handler).tool_call(
            system="s",
            prompt="p",
            tool_name="draft_survey_template",
            tool_description="d",
            input_schema={},
        )


async def test_timeout_produces_a_named_error_not_a_blank_line():
    """str(ReadTimeout) is empty; a raw format once logged a blank line and surfaced as
    "could not reach" while the model was merely slow. The error must say timeout."""

    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("")

    client = OpenAICompatibleLLMClient(
        base_url="http://backup.local/v1",
        api_key="",
        model="slow-model",
        timeout_seconds=90.0,
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(LLMError, match="timed out after 90"):
        await client.tool_turn(system="s", messages=[], tools=[])


def test_timeout_is_configurable_with_a_fast_connect():
    """A slow local model gets a generous read window; a genuinely unreachable
    endpoint still fails on the short connect timeout."""
    client = OpenAICompatibleLLMClient(
        base_url="http://backup.local/v1", api_key="", model="m", timeout_seconds=300.0
    )
    assert client._timeout.read == 300.0
    assert client._timeout.connect == 10.0
