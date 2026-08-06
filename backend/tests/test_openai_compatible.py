"""Provider tests: the failover wrapper and the OpenAI-compatible client.

All offline — the OpenAI-compatible client is driven through an httpx MockTransport, so no
network or API key is touched, and the failover wrapper uses in-memory doubles.
"""

import json
from typing import Any

import httpx
import pytest

from app.llm.client import LLMError, ToolTurn
from app.llm.failover import FailoverLLM
from app.llm.openai_compatible import OpenAICompatibleLLMClient

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
            raise LLMError("tier down")
        assert self._payload is not None
        return self._payload

    async def tool_turn(self, **_: Any) -> ToolTurn:
        self.tool_turn_calls += 1
        if self._fail:
            raise LLMError("tier down")
        assert self._turn is not None
        return self._turn


_ARGS: dict[str, Any] = dict(
    system="s", prompt="p", tool_name="t", tool_description="d", input_schema={}, max_tokens=16
)
_TURN_ARGS: dict[str, Any] = dict(system="s", messages=[], tools=[], max_tokens=16)


async def test_failover_prefers_the_first_tier_and_never_touches_the_second():
    tier1 = _StubLLM(payload={"ok": True}, turn=ToolTurn("hi", "move_on", {}))
    tier2 = _StubLLM(payload={"ok": False}, turn=ToolTurn("no", "move_on", {}))
    failover = FailoverLLM(tier1, tier2)

    assert await failover.tool_call(**_ARGS) == {"ok": True}
    assert await failover.tool_turn(**_TURN_ARGS) == ToolTurn("hi", "move_on", {})
    assert (tier2.tool_call_calls, tier2.tool_turn_calls) == (0, 0)


async def test_failover_uses_the_second_tier_when_the_first_fails():
    tier1 = _StubLLM(fail=True)
    tier2 = _StubLLM(payload={"from": "tier2"}, turn=ToolTurn("hey", "record_answer", {"v": 1}))
    failover = FailoverLLM(tier1, tier2)

    assert await failover.tool_call(**_ARGS) == {"from": "tier2"}
    assert await failover.tool_turn(**_TURN_ARGS) == ToolTurn("hey", "record_answer", {"v": 1})
    assert (tier1.tool_call_calls, tier1.tool_turn_calls) == (1, 1)
    assert (tier2.tool_call_calls, tier2.tool_turn_calls) == (1, 1)


async def test_failover_propagates_a_last_tier_failure_loudly():
    failover = FailoverLLM(_StubLLM(fail=True), _StubLLM(fail=True))
    with pytest.raises(LLMError):
        await failover.tool_call(**_ARGS)


async def test_failover_chains_through_to_the_third_tier():
    """OpenAI -> Groq -> OpenRouter: both earlier tiers fail, the third answers."""
    tier1 = _StubLLM(fail=True)
    tier2 = _StubLLM(fail=True)
    tier3 = _StubLLM(payload={"from": "t3"}, turn=ToolTurn("ok", "move_on", {}))
    failover = FailoverLLM(tier1, tier2, tier3)

    assert await failover.tool_call(**_ARGS) == {"from": "t3"}
    assert await failover.tool_turn(**_TURN_ARGS) == ToolTurn("ok", "move_on", {})
    assert tier1.tool_call_calls == tier2.tool_call_calls == tier3.tool_call_calls == 1


async def test_failover_stops_at_the_first_healthy_tier():
    tier1 = _StubLLM(fail=True)
    tier2 = _StubLLM(payload={"from": "t2"}, turn=ToolTurn("ok", "move_on", {}))
    tier3 = _StubLLM(payload={"from": "t3"}, turn=ToolTurn("no", "move_on", {}))
    failover = FailoverLLM(tier1, tier2, tier3)

    assert await failover.tool_call(**_ARGS) == {"from": "t2"}
    assert tier3.tool_call_calls == 0  # the third tier is never reached


async def test_failover_propagates_the_last_error_when_every_tier_fails():
    failover = FailoverLLM(_StubLLM(fail=True), _StubLLM(fail=True), _StubLLM(fail=True))
    with pytest.raises(LLMError):
        await failover.tool_turn(**_TURN_ARGS)


def test_failover_needs_at_least_one_client():
    with pytest.raises(ValueError):
        FailoverLLM()


# ---------------------------------------------------------------- OpenAI-compatible client


def _client(handler: Any) -> OpenAICompatibleLLMClient:
    return OpenAICompatibleLLMClient(
        base_url="http://tier.local/v1",
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
        base_url="http://tier.local/v1",
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
        base_url="http://tier.local/v1", api_key="", model="m", timeout_seconds=300.0
    )
    assert client._timeout.read == 300.0
    assert client._timeout.connect == 10.0


async def test_tool_call_in_a_fenced_block_or_prose_is_salvaged():
    """Local models wrap the call in ```json fences or lead-in prose; both recover."""
    fenced = 'Here you go:\n```json\n{"name": "move_on", "arguments": {"question_id": "q"}}\n```'
    prose = 'Sure! I will record that. {"name": "record_answer", "arguments": {"value": 4}} Done.'

    def make(content: str):
        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

        return handler

    turn = await _client(make(fenced)).tool_turn(system="s", messages=[], tools=[])
    assert (turn.tool_name, turn.tool_input) == ("move_on", {"question_id": "q"})

    turn = await _client(make(prose)).tool_turn(system="s", messages=[], tools=[])
    assert (turn.tool_name, turn.tool_input) == ("record_answer", {"value": 4})


async def test_no_tool_call_raises_the_retryable_error_type():
    """The engine retries a chatty turn but must never retry a timeout — the two need
    distinguishable types."""
    from app.llm.client import NoToolCallError

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": "just chat"}}]})

    with pytest.raises(NoToolCallError):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])


async def test_a_turn_cut_off_at_the_token_limit_is_not_retryable():
    """finish_reason "length" means the tokens ran out, not that the model declined to
    act. Retrying that with a nudge stops in the same place, so it must not arrive as a
    NoToolCallError."""
    from app.llm.client import NoToolCallError, TruncatedTurnError

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": '{"name": "record_'}, "finish_reason": "length"}
                ]
            },
        )

    with pytest.raises(TruncatedTurnError, match="token limit"):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])
    # A subclass of LLMError so failover still moves on, but never of the retryable type.
    assert issubclass(TruncatedTurnError, LLMError)
    assert not issubclass(TruncatedTurnError, NoToolCallError)


async def test_a_complete_call_in_a_truncated_turn_is_still_salvaged():
    """Truncation is checked after salvage: the model can finish the call and then be cut
    off mid-prose, and that call is perfectly usable."""

    complete_call = json.dumps({"name": "record_answer", "arguments": {"value": 4}})

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"content": f"{complete_call} and then it ran ou"},
                        "finish_reason": "length",
                    }
                ]
            },
        )

    turn = await _client(handler).tool_turn(system="s", messages=[], tools=[])
    assert (turn.tool_name, turn.tool_input) == ("record_answer", {"value": 4})


@pytest.mark.parametrize(
    ("label", "body"),
    [
        ("a bare list", []),
        ("a bare string", "nope"),
        ("a non-dict choice", {"choices": ["record_answer"]}),
        ("a string message", {"choices": [{"message": "record_answer"}]}),
        ("string tool_calls entries", {"choices": [{"message": {"tool_calls": ["record"]}}]}),
        ("tool_calls as an object", {"choices": [{"message": {"tool_calls": {"f": {}}}}]}),
        ("a string function", {"choices": [{"message": {"tool_calls": [{"function": "x"}]}}]}),
    ],
)
async def test_a_malformed_provider_body_stays_inside_the_error_type(label: str, body: Any) -> None:
    """These endpoints are third-party and sometimes answer with JSON that is not the
    Chat Completions shape. Walking it optimistically raised AttributeError/KeyError,
    which FailoverLLM does not catch — so one bad body killed the request instead of
    moving to the next provider."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    with pytest.raises(LLMError):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])


async def test_a_non_json_body_stays_inside_the_error_type():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>gateway</html>")

    with pytest.raises(LLMError, match="non-JSON"):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])


async def test_a_malformed_body_falls_through_to_the_next_provider():
    """The point of the shape checks: a broken tier must not abort the chain."""

    def broken(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": ["record_answer"]})

    def working(_: httpx.Request) -> httpx.Response:
        return _tool_response("move_on", {"question_id": "q"})

    chain = FailoverLLM(_client(broken), _client(working))
    turn = await chain.tool_turn(system="s", messages=[], tools=[])
    assert turn.tool_name == "move_on"


@pytest.mark.parametrize(
    ("label", "content"),
    [
        (
            "a brace inside an earlier quoted string",
            'The format is "{name}" — here you go: '
            '{"name": "move_on", "arguments": {"question_id": "q"}}',
        ),
        (
            "a non-tool object emitted first",
            '{"thinking": "they gave a role"} '
            '{"name": "move_on", "arguments": {"question_id": "q"}}',
        ),
        (
            "literal braces in the prose first",
            'Use {curly} braces for JSON. {"name": "move_on", "arguments": {"question_id": "q"}}',
        ),
    ],
)
async def test_a_call_after_an_earlier_brace_is_still_salvaged(label: str, content: str) -> None:
    """Salvage used to look at the first balanced {...} only, and started scanning at the
    first '{' — so a brace inside earlier prose or a leading thinking object swallowed the
    real call, and a turn the model got right was thrown away as 'no tool call'."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    turn = await _client(handler).tool_turn(system="s", messages=[], tools=[])
    assert (turn.tool_name, turn.tool_input) == ("move_on", {"question_id": "q"})


@pytest.mark.parametrize(
    ("label", "content"),
    [
        ("unclosed object", '{"name": "move_on", "arguments": {'),
        ("no object at all", "I think they mean the packing line."),
        ("an object with no name", '{"arguments": {"value": "x"}}'),
    ],
)
async def test_salvage_still_refuses_what_is_not_a_tool_call(label: str, content: str) -> None:
    """Scanning more candidates must not mean accepting looser ones."""
    from app.llm.client import NoToolCallError

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    with pytest.raises(NoToolCallError):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])


async def test_a_tier_records_its_token_usage(caplog):
    """Any tier can serve any live turn, and until this was added those tokens were
    spent with no record whatsoever."""
    import logging

    def handler(_: httpx.Request) -> httpx.Response:
        body = json.loads(_tool_response("move_on", {"question_id": "q"}).content)
        body["usage"] = {"prompt_tokens": 812, "completion_tokens": 37, "total_tokens": 849}
        return httpx.Response(200, json=body)

    with caplog.at_level(logging.INFO, logger="app.llm.openai_compatible"):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])

    usage = [r.getMessage() for r in caplog.records if "usage=" in r.getMessage()]
    assert len(usage) == 1, usage
    assert "nemotron-test" in usage[0]  # which tier spent it
    assert "849" in usage[0]


async def test_a_tier_that_omits_usage_still_logs_cleanly(caplog):
    """Not every OpenAI-compatible endpoint returns a usage block. Recording None is the
    honest answer; raising over optional provider metadata would not be."""
    import logging

    def handler(_: httpx.Request) -> httpx.Response:
        return _tool_response("move_on", {"question_id": "q"})

    with caplog.at_level(logging.INFO, logger="app.llm.openai_compatible"):
        turn = await _client(handler).tool_turn(system="s", messages=[], tools=[])

    assert turn.tool_name == "move_on"
    assert any("usage=None" in r.getMessage() for r in caplog.records)
