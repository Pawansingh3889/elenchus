"""Provider tests: the failover wrapper and the OpenAI-compatible client.

All offline: the OpenAI-compatible client is driven through an httpx MockTransport, so no
network or API key is touched, and the failover wrapper uses in-memory doubles.
"""

import json
from typing import Any

import httpx
import pytest

from app.llm.client import LLMError, NoToolCallError, ToolTurn, TruncatedTurnError
from app.llm.failover import FailoverLLM
from app.llm.openai_compatible import OpenAICompatibleLLMClient


@pytest.fixture(autouse=True)
def _no_retry_backoff(monkeypatch):
    """The retry loop sleeps between attempts; the suite should not."""
    monkeypatch.setattr("app.llm.openai_compatible.RETRY_BACKOFF_SECONDS", 0)


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
    # The request forced exactly the tool we asked for, and exactly one call of it.
    assert seen["body"]["tool_choice"] == {
        "type": "function",
        "function": {"name": "draft_survey_template"},
    }
    assert seen["body"]["tools"][0]["function"]["name"] == "draft_survey_template"
    assert seen["body"]["parallel_tool_calls"] is False


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
    # "required" means at least one call; this is the other half of "exactly one".
    assert seen["body"]["parallel_tool_calls"] is False


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


# ------------------------------------------------- exactly one tool call per turn


async def test_a_turn_yields_one_tool_even_if_the_model_sends_two():
    """The deleted Anthropic-era guard, restored for the OpenAI shape. Taking the first
    of two calls silently discards the second, and when [move_on, record_answer]
    arrives, the discarded half is the respondent's answer. Refusing is retryable: the
    model is responsive, just off-script, which is NoToolCallError's exact case."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "tool_calls": [
                                {"function": {"name": "move_on", "arguments": "{}"}},
                                {
                                    "function": {
                                        "name": "record_answer",
                                        "arguments": json.dumps({"value": True}),
                                    }
                                },
                            ],
                        }
                    }
                ]
            },
        )

    with pytest.raises(NoToolCallError, match="2 tool calls"):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])


# ------------------------------------------------------------- transient retries


def _flaky(responses: list[httpx.Response | Exception]):
    """A handler that serves the scripted responses in order, counting attempts."""
    calls = {"n": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        index = min(calls["n"], len(responses) - 1)
        calls["n"] += 1
        item = responses[index]
        if isinstance(item, Exception):
            raise item
        return item

    return handler, calls


async def test_a_rate_limited_call_is_retried_in_tier():
    """The removed SDK client retried transient failures (max_retries=2); a survey turn
    must not surface a 503 to the respondent over one momentary 429."""
    handler, calls = _flaky(
        [httpx.Response(429, text="slow down"), _tool_response("move_on", {"question_id": "q"})]
    )
    turn = await _client(handler).tool_turn(system="s", messages=[], tools=[])
    assert turn.tool_name == "move_on"
    assert calls["n"] == 2


async def test_a_connection_error_is_retried_in_tier():
    handler, calls = _flaky(
        [httpx.ConnectError("refused"), _tool_response("move_on", {"question_id": "q"})]
    )
    turn = await _client(handler).tool_turn(system="s", messages=[], tools=[])
    assert turn.tool_name == "move_on"
    assert calls["n"] == 2


async def test_retries_run_out_and_the_typed_error_survives():
    handler, calls = _flaky([httpx.Response(503, text="upstream unavailable")])
    with pytest.raises(LLMError, match="503"):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])
    assert calls["n"] == 3  # one call plus two retries, the SDK's old budget


async def test_a_read_timeout_is_never_retried_in_tier():
    """Each attempt can cost the full LLM_TIER<n>_TIMEOUT_SECONDS; a model that is
    merely slow does not get faster for being asked twice."""
    handler, calls = _flaky([httpx.ReadTimeout("")])
    with pytest.raises(LLMError, match="timed out"):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])
    assert calls["n"] == 1


async def test_a_bad_request_is_never_retried():
    """Retrying a 400 resends the same bad request."""
    handler, calls = _flaky([httpx.Response(400, text="bad schema")])
    with pytest.raises(LLMError, match="400"):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])
    assert calls["n"] == 1


# ------------------------------------------------- failed calls still reach the ledger


@pytest.fixture
def ledger_file(tmp_path, monkeypatch):
    """Point the ledger at a private file so this test can read what was booked."""
    from app.config import get_settings

    path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("LLM_LEDGER_PATH", str(path))
    get_settings.cache_clear()
    yield path
    get_settings.cache_clear()


async def test_failed_calls_leave_ledger_rows_too(ledger_file):
    """A ledger that records only successes cannot explain a cost spike caused by an
    afternoon of 429s pushing traffic to a priced tier."""
    handler, _ = _flaky(
        [httpx.Response(429, text="slow down"), _tool_response("move_on", {"question_id": "q"})]
    )
    await _client(handler).tool_turn(system="s", messages=[], tools=[])

    rows = [json.loads(line) for line in ledger_file.read_text(encoding="utf-8").splitlines()]
    assert [row["status"] for row in rows] == [429, 200]
    assert rows[0]["error"] == "slow down"
    assert rows[1]["error"] is None


async def test_a_call_that_never_connected_is_booked_with_status_zero(ledger_file):
    handler, _ = _flaky([httpx.ConnectError("refused")])
    with pytest.raises(LLMError):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])

    rows = [json.loads(line) for line in ledger_file.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3  # every attempt is an event, not just the last
    assert all(row["status"] == 0 for row in rows)
    assert all("refused" in row["error"] for row in rows)


# ------------------------------------------- failover leaves the nudge to the engine


class _ChattyLLM(_StubLLM):
    """A tier that is up but answered with prose instead of a tool call."""

    async def tool_turn(self, **_: Any) -> ToolTurn:
        self.tool_turn_calls += 1
        raise NoToolCallError("LLM tier returned no tool call.")

    async def tool_call(self, **_: Any) -> dict[str, Any]:
        self.tool_call_calls += 1
        raise NoToolCallError("LLM tier returned no tool call.")


async def test_a_chatty_tier_is_not_failed_over_when_the_caller_owns_the_retry():
    """A model that chatted is not a downed provider. The engine answers this error
    with one nudged retry through the same chain; cascading instead silently handed
    the respondent's turn to ever weaker tiers while the healthy one was fine."""
    tier1 = _ChattyLLM()
    tier2 = _StubLLM(turn=ToolTurn("hi", "move_on", {}))
    failover = FailoverLLM(tier1, tier2)

    with pytest.raises(NoToolCallError):
        await failover.tool_turn(**_TURN_ARGS, cascade_on_no_tool_call=False)
    assert tier2.tool_turn_calls == 0


async def test_a_chatty_tier_falls_over_for_a_caller_that_cannot_retry():
    """The other side of the same flag, and the reason it is a flag at all. Template
    drafting and run summarising call tool_turn with no retry of their own, so the next
    tier is their only recovery. Making the carve-out unconditional took that away: one
    chatty turn from tier 1 became an immediate 503 with healthy tiers left untried."""
    tier1 = _ChattyLLM()
    tier2 = _StubLLM(turn=ToolTurn("hi", "move_on", {}))
    failover = FailoverLLM(tier1, tier2)

    assert await failover.tool_turn(**_TURN_ARGS) == ToolTurn("hi", "move_on", {})
    assert (tier1.tool_turn_calls, tier2.tool_turn_calls) == (1, 1)


async def test_a_downed_tier_cascades_even_when_the_caller_owns_the_retry():
    """The carve-out is about chatter, not about health. A nudge cannot revive a tier
    that is not answering, so opting out of it must not opt out of failover itself."""
    tier1 = _StubLLM(fail=True)
    tier2 = _StubLLM(turn=ToolTurn("hi", "move_on", {}))
    failover = FailoverLLM(tier1, tier2)

    turn = await failover.tool_turn(**_TURN_ARGS, cascade_on_no_tool_call=False)
    assert turn == ToolTurn("hi", "move_on", {})


async def test_a_chatty_tier_still_cascades_on_the_one_shot_path():
    """tool_call has no nudge mechanism, so the next tier is its only recovery."""
    tier1 = _ChattyLLM()
    tier2 = _StubLLM(payload={"from": "t2"})
    failover = FailoverLLM(tier1, tier2)

    assert await failover.tool_call(**_ARGS) == {"from": "t2"}
    assert tier1.tool_call_calls == 1


# ------------------------------------------------------------------------- streaming


def _sse(*events: dict[str, Any] | str) -> httpx.Response:
    """A server-sent event stream, the way a streaming tier sends one."""
    body = "".join(f"data: {e if isinstance(e, str) else json.dumps(e)}\n\n" for e in events)
    return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body.encode())


def _tool_delta(name: str | None = None, arguments: str | None = None) -> dict[str, Any]:
    function: dict[str, Any] = {}
    if name is not None:
        function["name"] = name
    if arguments is not None:
        function["arguments"] = arguments
    return {
        "choices": [{"index": 0, "delta": {"tool_calls": [{"index": 0, "function": function}]}}]
    }


_FINISH: dict[str, Any] = {"choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}]}
# The final chunk gpt-5.5 sent a live probe on 13 Sep 2026, trimmed: no choices, only usage.
_USAGE: dict[str, Any] = {
    "choices": [],
    "usage": {
        "prompt_tokens": 166,
        "completion_tokens": 17,
        "prompt_tokens_details": {"cached_tokens": 0},
        "completion_tokens_details": {"reasoning_tokens": 0},
    },
}


def _booked(path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


async def test_every_call_asks_to_stream_with_usage():
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return _tool_response("move_on", {"question_id": "q"})

    await _client(handler).tool_turn(system="s", messages=[], tools=[])
    assert seen["body"]["stream"] is True
    assert seen["body"]["stream_options"] == {"include_usage": True}


async def test_a_streamed_tool_call_is_reassembled_from_its_fragments():
    """The shape gpt-5.5 streamed on 13 Sep 2026: the name once, then the arguments in
    pieces, then a finish chunk and a usage chunk with no choices."""

    def handler(_: httpx.Request) -> httpx.Response:
        return _sse(
            _tool_delta(name="record_answer", arguments=""),
            _tool_delta(arguments='{"val'),
            _tool_delta(arguments='ue": "Line'),
            _tool_delta(arguments=' lead"}'),
            _FINISH,
            _USAGE,
            "[DONE]",
        )

    turn = await _client(handler).tool_turn(system="s", messages=[], tools=[])
    assert turn == ToolTurn(text="", tool_name="record_answer", tool_input={"value": "Line lead"})


async def test_streamed_text_is_joined_and_kept_beside_the_tool_call():
    def handler(_: httpx.Request) -> httpx.Response:
        return _sse(
            {"choices": [{"index": 0, "delta": {"content": "Thanks"}}]},
            {"choices": [{"index": 0, "delta": {"content": " for that."}}]},
            _tool_delta(name="move_on", arguments='{"question_id": "q"}'),
            _FINISH,
            "[DONE]",
        )

    turn = await _client(handler).tool_turn(system="s", messages=[], tools=[])
    assert turn.text == "Thanks for that."
    assert turn.tool_name == "move_on"


async def test_a_tool_call_streamed_as_text_is_still_salvaged():
    def handler(_: httpx.Request) -> httpx.Response:
        call = '{"name": "move_on", "arguments": {"question_id": "q"}}'
        return _sse({"choices": [{"index": 0, "delta": {"content": call}}]}, "[DONE]")

    turn = await _client(handler).tool_turn(system="s", messages=[], tools=[])
    assert turn.tool_name == "move_on"


async def test_a_stream_that_runs_out_of_tokens_is_a_truncated_turn():
    def handler(_: httpx.Request) -> httpx.Response:
        return _sse(
            {"choices": [{"index": 0, "delta": {"content": "I think"}, "finish_reason": "length"}]},
            "[DONE]",
        )

    with pytest.raises(TruncatedTurnError):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])


async def test_a_non_json_event_fails_loudly_and_is_booked(ledger_file):
    def handler(_: httpx.Request) -> httpx.Response:
        return _sse("not json at all")

    with pytest.raises(LLMError, match="non-JSON event"):
        await _client(handler).tool_turn(system="s", messages=[], tools=[])
    (row,) = _booked(ledger_file)
    assert row["error"] == "non-JSON event"


async def test_a_streamed_call_books_its_usage_and_first_token_time(ledger_file):
    def handler(_: httpx.Request) -> httpx.Response:
        return _sse(_tool_delta(name="move_on", arguments='{"question_id": "q"}'), _FINISH, _USAGE)

    await _client(handler).tool_turn(system="s", messages=[], tools=[])
    (row,) = _booked(ledger_file)
    assert (row["prompt_tokens"], row["completion_tokens"]) == (166, 17)
    assert isinstance(row["first_token_ms"], int)
    assert 0 <= row["first_token_ms"] <= row["latency_ms"]


async def test_a_stream_cut_before_its_usage_chunk_is_booked_as_unmetered(ledger_file):
    """Usage comes on the last chunk only, and OpenAI's own docs warn an interrupted
    stream may never send it. The turn still stands; its tokens are unknown, not zero."""

    def handler(_: httpx.Request) -> httpx.Response:
        return _sse(_tool_delta(name="move_on", arguments='{"question_id": "q"}'), _FINISH)

    turn = await _client(handler).tool_turn(system="s", messages=[], tools=[])
    assert turn.tool_name == "move_on"
    (row,) = _booked(ledger_file)
    assert row["prompt_tokens"] is None
    assert row["first_token_ms"] is not None


async def test_a_tier_that_ignores_stream_is_still_understood(ledger_file):
    """Some OpenAI-compatible servers answer in one piece whatever was asked. That is a
    valid answer with no first-token time to give."""

    def handler(_: httpx.Request) -> httpx.Response:
        return _tool_response("move_on", {"question_id": "q"})

    turn = await _client(handler).tool_turn(system="s", messages=[], tools=[])
    assert turn.tool_name == "move_on"
    (row,) = _booked(ledger_file)
    assert row["first_token_ms"] is None


async def test_a_stream_that_drops_mid_answer_is_retried():
    """Holding the connection for the whole answer makes a mid-response hang-up more
    likely than it was, so it has to stay in the cheap-to-retry class."""
    attempts = {"n": 0}

    async def dropped():
        yield b"data: " + json.dumps(_tool_delta(name="move_on")).encode() + b"\n\n"
        raise httpx.RemoteProtocolError("peer closed connection without sending complete body")

    def handler(_: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] == 1:
            return httpx.Response(
                200, headers={"content-type": "text/event-stream"}, content=dropped()
            )
        return _sse(
            _tool_delta(name="move_on", arguments='{"question_id": "q"}'), _FINISH, "[DONE]"
        )

    turn = await _client(handler).tool_turn(system="s", messages=[], tools=[])
    assert turn.tool_name == "move_on"
    assert attempts["n"] == 2
