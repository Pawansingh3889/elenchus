"""The one LLM client, speaking the OpenAI Chat Completions API.

Every configured tier answers this protocol, whether it is OpenAI itself, Groq,
OpenRouter, a self-hosted vLLM or a local Ollama. One instance is built per enabled tier,
differing only in base URL, key, model and timeout, so the conduct engine and generation
service cannot tell which tier answered. Transport failures become one typed ``LLMError``
and a malformed or missing tool call fails loudly rather than degrading.

A knowing deviation, recorded here so it is a decision rather than a discovery:
ARCHITECTURE.md 3.1 says "Never regex/parse structured data out of prose", and
``_salvage_from_content`` below does precisely that. It exists because the lower tiers
are free or locally served models that routinely write the tool call into the message
text instead of into ``tool_calls``, and refusing to salvage would mean refusing to run
whenever the chain reaches them. The mitigation is that salvage only ever *proposes* a
tool call: the payload is validated against the same schema as any other, and the engine
rejects it identically if it does not fit.
"""

import asyncio
import json
import logging
import re
import time
from collections.abc import Iterator
from typing import Any, cast

import httpx

from app.llm import ledger
from app.llm.client import LLMError, NoToolCallError, ToolTurn, TruncatedTurnError

logger = logging.getLogger("app.llm.openai_compatible")


def _balanced_objects(text: str) -> Iterator[str]:
    """Every balanced top-level {...} in the text, in order.

    Brace-counting with string awareness — enough to lift JSON objects out of
    surrounding prose without a full parser.

    Two details earn their keep. The scan starts at the beginning of the text rather
    than at the first ``{``: skipping ahead means a brace inside an earlier quoted
    string ("the format is \"{name}\"") is mistaken for the start of an object, and the
    real call after it is never seen. And every object is yielded, not just the first,
    because models routinely emit something else first — a thinking object, an example —
    and the caller has no way to know which one is the tool call until it tries.
    """
    depth, start, in_string, escaped = 0, None, False, False
    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}" and depth:
            depth -= 1
            if depth == 0 and start is not None:
                yield text[start : index + 1]
                start = None


# A local CPU-served model (the very case the last tier exists for) can legitimately take
# well over a minute on a cold load or a long survey, so the read timeout is generous
# and configurable (LLM_TIER<n>_TIMEOUT_SECONDS). Connecting, by contrast, should be
# near-instant — a short connect timeout keeps a *genuinely* unreachable endpoint from
# stalling a request for the full read window.
DEFAULT_TIMEOUT_SECONDS = 120.0
CONNECT_TIMEOUT_SECONDS = 10.0

# In-tier retry budget for transient failures, restoring what the removed SDK client did
# with max_retries=2: three attempts in all. Only failures that are cheap and usually
# passing qualify: nothing connected, the server hung up mid-response, or it answered
# 429/5xx. A read timeout is deliberately NOT among them, because each attempt may cost
# the full LLM_TIER<n>_TIMEOUT_SECONDS and a model that is merely slow does not get
# faster for being asked twice. A 4xx other than 429 resends the same bad request, so it
# is not retried either.
MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 1.0
_RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


class _Transient(Exception):
    """Internal: a failure worth another attempt, carrying the typed error to raise
    when the attempts run out. Never escapes ``_post``."""

    def __init__(self, error: LLMError) -> None:
        self.error = error


class OpenAICompatibleLLMClient:
    """Force one schema-constrained tool call out of an OpenAI-compatible endpoint."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        transport: httpx.AsyncBaseTransport | None = None,
        tier: int = 0,
    ) -> None:
        if not base_url or not model:
            raise LLMError("This LLM tier is enabled but its base_url/model are not configured.")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = httpx.Timeout(timeout_seconds, connect=CONNECT_TIMEOUT_SECONDS)
        self._transport = transport  # injectable so tests need no network
        # Which tier this client is in the chain, so the ledger can price the call. The
        # factory always knows it; the default is for tests that build a client directly,
        # and 0 records honestly as "no economics configured" rather than pricing the
        # call as tier 1's.
        self._tier = tier

    async def _post(self, payload: dict[str, Any], op: str = "unknown") -> dict[str, Any]:
        """POST once, retrying the cheap transient failures, booking every attempt."""
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return await self._attempt(payload, op)
            except _Transient as exc:
                if attempt == MAX_ATTEMPTS:
                    raise exc.error from None
                logger.warning(
                    "llm tier transient failure, retrying (attempt %d of %d): %s",
                    attempt,
                    MAX_ATTEMPTS,
                    exc.error,
                )
                await asyncio.sleep(RETRY_BACKOFF_SECONDS * attempt)
        raise LLMError("unreachable")  # the loop either returns or raises

    async def _attempt(self, payload: dict[str, Any], op: str) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        # Monotonic, not wall clock: this becomes the cost of a locally served call, and
        # a clock adjustment mid-request would otherwise price the turn as negative.
        started = time.monotonic()

        def book(status: int, usage: Any, error: str | None) -> None:
            # Every attempt leaves a row, failures included. A ledger that only records
            # successes cannot explain a cost spike caused by an afternoon of 429s
            # pushing traffic to a priced tier: the calls that drove the spend would be
            # the only ones missing from the record built to explain it.
            ledger.record(
                tier=self._tier,
                model=self._model,
                op=op,
                usage=usage,
                latency_ms=int((time.monotonic() - started) * 1000),
                status=status,
                error=error,
            )

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions", json=payload, headers=headers
                )
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.RemoteProtocolError) as exc:
            # Nothing connected, or the server hung up mid-response: cheap to retry
            # (the connect budget is seconds) and usually passing.
            logger.error("llm tier call failed: %r", exc)
            book(0, None, repr(exc))
            raise _Transient(LLMError(f"Could not reach the LLM tier: {exc!r}")) from exc
        except httpx.TimeoutException as exc:
            # A read timeout is the one transport failure not retried in-tier: each
            # attempt may cost the full read budget, and a model that is merely slow
            # does not get faster for being asked twice. str(ReadTimeout) is usually
            # empty, which once surfaced as a blank "could not reach": name the failure.
            logger.error("llm tier timed out: %r", exc)
            book(0, None, f"timed out after {self._timeout.read}s")
            raise LLMError(
                f"LLM tier timed out after {self._timeout.read}s. The model may be "
                "loading or too slow for the configured LLM_TIER<n>_TIMEOUT_SECONDS."
            ) from exc
        except httpx.HTTPError as exc:
            # repr, not str: several httpx errors stringify to "".
            logger.error("llm tier call failed: %r", exc)
            book(0, None, repr(exc))
            raise LLMError(f"Could not reach the LLM tier: {exc!r}") from exc
        if response.status_code >= 400:
            logger.error("llm tier returned %s: %s", response.status_code, response.text[:200])
            book(response.status_code, None, response.text[:200])
            error = LLMError(
                f"LLM tier rejected the request ({response.status_code}): {response.text[:200]}"
            )
            if response.status_code in _RETRYABLE_STATUSES:
                raise _Transient(error)
            raise error
        try:
            body = response.json()
        except ValueError as exc:
            book(response.status_code, None, "non-JSON body")
            raise LLMError(f"LLM tier returned a non-JSON body: {response.text[:200]}") from exc
        if not isinstance(body, dict):
            book(response.status_code, None, f"{type(body).__name__} body")
            raise LLMError(f"LLM tier returned {type(body).__name__}, expected a JSON object.")
        # Logged after parsing so the token usage is in reach: any tier can serve any
        # live turn, and until now those tokens were spent with no record at all. One format
        # across tiers means one grep finds every tier's spend.
        #
        # `.get` is not a no-fallbacks shrug here: usage is optional provider metadata that
        # is recorded and never acted on, unlike the required data ARCHITECTURE.md 4 is
        # about. A tier that omits it logs usage=None, which is the honest answer.
        logger.info(
            "llm tier call model=%s status=%s usage=%s",
            self._model,
            response.status_code,
            body.get("usage"),
        )
        # The durable half of the same fact. The log line is for reading now; this is for
        # answering "what did that survey cost, on which model" months from now, when the
        # logs have rotated away.
        book(response.status_code, body.get("usage"), None)
        return cast("dict[str, Any]", body)

    @staticmethod
    def _salvage_from_content(said: Any) -> list[dict[str, Any]]:
        """Local models often write the tool call INTO the text instead of tool_calls.

        Recover a tool-call-shaped JSON object ({"name": ..., "arguments"/"parameters":
        {...}}) from the content: the whole text, a fenced ``` block, or any JSON object
        embedded in prose ("Sure! {...}"). The first candidate with that exact shape
        wins; anything else stays a hard failure.
        """
        if not isinstance(said, str):
            return []
        text = said.strip()

        candidates = [text]
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
        if fence:
            candidates.append(fence.group(1))
        candidates.extend(_balanced_objects(text))

        for candidate in candidates:
            try:
                parsed = json.loads(candidate, strict=False)
            except json.JSONDecodeError:
                continue
            if not isinstance(parsed, dict) or not isinstance(parsed.get("name"), str):
                continue
            arguments = parsed.get("arguments", parsed.get("parameters", {}))
            if not isinstance(arguments, dict):
                continue
            return [{"function": {"name": parsed["name"], "arguments": json.dumps(arguments)}}]
        return []

    @staticmethod
    def _first_tool_call(data: dict[str, Any]) -> tuple[str, dict[str, Any], str]:
        """Pull (tool name, parsed arguments, spoken text) from the first choice.

        Every hop is shape-checked. These endpoints are third-party and occasionally
        answer with something that is JSON but not the Chat Completions shape; walking
        it optimistically raised AttributeError/KeyError, which is not an ``LLMError``
        and so aborted the whole failover chain instead of moving to the next provider.
        """
        choices = data.get("choices") or []
        if not isinstance(choices, list) or not choices:
            raise LLMError("LLM tier returned no choices.")
        if not isinstance(choices[0], dict):
            raise LLMError("LLM tier returned a malformed choice.")
        message = choices[0].get("message") or {}
        if not isinstance(message, dict):
            raise LLMError("LLM tier returned a malformed message.")
        said = message.get("content")
        tool_calls = message.get("tool_calls") or []
        if not isinstance(tool_calls, list):
            raise LLMError("LLM tier returned a malformed tool_calls field.")
        if not tool_calls:
            tool_calls = OpenAICompatibleLLMClient._salvage_from_content(said)
            if tool_calls:
                said = ""  # the content WAS the tool call; there is nothing spoken
        if not tool_calls:
            # Ran out of tokens rather than declined to act. Kept apart from
            # NoToolCallError because the engine retries that one with a nudge, and a
            # retry at the same budget stops in exactly the same place: a wasted turn,
            # then the same failure. Salvage is attempted first, since a truncated turn
            # can still carry a complete tool call in the text it managed to write.
            if choices[0].get("finish_reason") == "length":
                raise TruncatedTurnError(
                    "LLM tier hit its token limit before completing a tool call."
                )
            raise NoToolCallError("LLM tier returned no tool call.")
        if len(tool_calls) > 1:
            # The request asks for exactly one call (parallel_tool_calls false), but not
            # every endpoint honours that flag. Taking the first and discarding the rest
            # silently threw away whichever action came second; when [move_on,
            # record_answer] arrived, the respondent's recorded answer was the part that
            # vanished. Refusing is the retryable kind of failure: the model is
            # responsive, it is just off-script, which is NoToolCallError's exact case.
            raise NoToolCallError(
                f"LLM tier returned {len(tool_calls)} tool calls; exactly one is allowed."
            )
        if not isinstance(tool_calls[0], dict):
            raise LLMError("LLM tier returned a malformed tool call.")
        function = tool_calls[0].get("function") or {}
        if not isinstance(function, dict):
            raise LLMError("LLM tier tool call has a malformed function field.")
        name = function.get("name")
        if not isinstance(name, str):
            raise LLMError("LLM tier tool call is missing a name.")
        raw_arguments = function.get("arguments", "{}")
        try:
            arguments = (
                json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
            )
        except json.JSONDecodeError as exc:
            raise LLMError(f"LLM tier tool arguments were not valid JSON: {exc}") from exc
        if not isinstance(arguments, dict):
            raise LLMError("LLM tier tool arguments were not a JSON object.")
        return name, cast("dict[str, Any]", arguments), said if isinstance(said, str) else ""

    @staticmethod
    def _as_openai_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Translate the engine's tool shape (name/description/input_schema) to OpenAI's."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool["input_schema"],
                },
            }
            for tool in tools
        ]

    async def tool_call(
        self,
        *,
        system: str,
        prompt: str,
        tool_name: str,
        tool_description: str,
        input_schema: dict[str, Any],
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "tools": self._as_openai_tools(
                [{"name": tool_name, "description": tool_description, "input_schema": input_schema}]
            ),
            "tool_choice": {"type": "function", "function": {"name": tool_name}},
            # One call, not several: the engines act on exactly one tool per turn, and
            # a provider that answers with two forces this client to choose for them.
            # Endpoints that do not know the flag ignore it; _first_tool_call refuses
            # multi-call answers regardless, so the guard holds either way.
            "parallel_tool_calls": False,
        }
        data = await self._post(payload, op="tool_call")
        name, arguments, _ = self._first_tool_call(data)
        if name != tool_name:
            raise LLMError(f"LLM tier called {name!r}, expected {tool_name!r}.")
        return arguments

    async def tool_turn(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        max_tokens: int = 1024,
    ) -> ToolTurn:
        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, *messages],
            "tools": self._as_openai_tools(tools),
            # "required" alone means at least one call, not exactly one. The second half
            # of "exactly" is parallel_tool_calls, and the belt for endpoints that
            # ignore it is _first_tool_call refusing multi-call answers.
            "tool_choice": "required",
            "parallel_tool_calls": False,
        }
        data = await self._post(payload, op="tool_turn")
        name, arguments, said = self._first_tool_call(data)
        return ToolTurn(text=said.strip(), tool_name=name, tool_input=arguments)
