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

Every call streams. That is for measurement, not for the respondent: the one number a
whole response cannot give is how long the model took before it produced anything, and
on a reasoning model that is nearly all of the wait (3.4 of 3.5 seconds on a live
gpt-5.5 tool call). The stream is assembled back into the unstreamed body shape before
anything reads it, so validation, salvage and failover see exactly what they saw before.
"""

import asyncio
import json
import logging
import re
import time
from collections.abc import Callable, Iterator
from typing import Any, cast

import httpx

from app.llm import ledger
from app.llm.client import (
    ContextWindowExceededError,
    LLMError,
    NoToolCallError,
    ToolTurn,
    TruncatedTurnError,
)
from app.llm.ledger import TierEconomics

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


def _one_piece(raw: str, fail: Callable[[str], None]) -> dict[str, Any]:
    """An unstreamed body, shape-checked the way every response was before streaming."""
    try:
        body = json.loads(raw)
    except ValueError as exc:
        fail("non-JSON body")
        raise LLMError(f"LLM tier returned a non-JSON body: {raw[:200]}") from exc
    if not isinstance(body, dict):
        fail(f"{type(body).__name__} body")
        raise LLMError(f"LLM tier returned {type(body).__name__}, expected a JSON object.")
    return cast("dict[str, Any]", body)


async def _assemble_stream(
    response: httpx.Response,
    mark_first_output: Callable[[], None],
    fail: Callable[[str], None],
) -> dict[str, Any]:
    """Rebuild one Chat Completions body from a server-sent event stream.

    The result has the unstreamed shape, so ``_first_tool_call`` validates a streamed turn
    exactly as it validated a whole one. Text arrives as fragments; a tool call arrives as
    fragments keyed by index, its name once and its arguments in pieces; ``finish_reason``
    comes on the last chunk that has one; and usage comes on a final chunk with no choices,
    or not at all if the stream is cut first.

    An event that is not a JSON object fails loudly. Anything else is read tolerantly,
    because the assembled body goes through the same strict checks as an unstreamed one.
    """
    content: list[str] = []
    calls: dict[int, dict[str, str]] = {}
    finish_reason: Any = None
    usage: Any = None
    async for line in response.aiter_lines():
        if not line.startswith("data:"):
            continue  # blank separators, keep-alive comments, event names
        data = line[len("data:") :].strip()
        if data == "[DONE]":
            break
        try:
            chunk = json.loads(data)
        except ValueError as exc:
            fail("non-JSON event")
            raise LLMError(f"LLM tier streamed a non-JSON event: {data[:200]}") from exc
        if not isinstance(chunk, dict):
            fail(f"{type(chunk).__name__} event")
            raise LLMError(f"LLM tier streamed {type(chunk).__name__}, expected a JSON object.")
        if chunk.get("usage") is not None:
            usage = chunk["usage"]
        choices = chunk.get("choices")
        for choice in choices if isinstance(choices, list) else []:
            if not isinstance(choice, dict):
                continue
            delta = choice.get("delta")
            delta = delta if isinstance(delta, dict) else {}
            text = delta.get("content")
            if isinstance(text, str) and text:
                mark_first_output()
                content.append(text)
            parts = delta.get("tool_calls")
            for part in parts if isinstance(parts, list) else []:
                if not isinstance(part, dict):
                    continue
                mark_first_output()
                index = part.get("index", 0)
                slot = calls.setdefault(
                    index if isinstance(index, int) else 0, {"name": "", "arguments": ""}
                )
                function = part.get("function")
                function = function if isinstance(function, dict) else {}
                if isinstance(function.get("name"), str):
                    slot["name"] += function["name"]
                if isinstance(function.get("arguments"), str):
                    slot["arguments"] += function["arguments"]
            if choice.get("finish_reason"):
                finish_reason = choice["finish_reason"]
    message: dict[str, Any] = {"content": "".join(content)}
    if calls:
        message["tool_calls"] = [
            {"function": {"name": slot["name"], "arguments": slot["arguments"] or "{}"}}
            for _, slot in sorted(calls.items())
        ]
    return {"choices": [{"message": message, "finish_reason": finish_reason}], "usage": usage}


def _request_of(payload: dict[str, Any]) -> dict[str, Any] | None:
    """What a chat call asked, exactly, for the trace; None for a call with no messages.

    The transport keys (model, stream, token limits) are left out: the model is on the span
    already, and the rest changes how an answer arrives, not what was asked.
    """
    if "messages" not in payload:
        return None
    return {key: payload[key] for key in ("messages", "tools", "tool_choice") if key in payload}


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
        prompt_cache: bool = False,
        max_completion_tokens: int = 4096,
        priced_as: TierEconomics | None = None,
        context_window: int | None = None,
    ) -> None:
        if not base_url or not model:
            raise LLMError("This LLM tier is enabled but its base_url/model are not configured.")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = httpx.Timeout(timeout_seconds, connect=CONNECT_TIMEOUT_SECONDS)
        self._transport = transport  # injectable so tests need no network
        self._tier = tier
        self._prompt_cache = prompt_cache
        self._max_completion_tokens = max_completion_tokens
        # Set for a client outside the tier chain, which the ledger cannot price by tier.
        self._priced_as = priced_as
        # None on a tier that has not stated one, which leaves _check_context_window
        # with nothing to check against rather than a guessed number to check against.
        self._context_window = context_window

    @property
    def model(self) -> str:
        return self._model

    async def _post(
        self,
        payload: dict[str, Any],
        op: str = "unknown",
        path: str = "/chat/completions",
        stream: bool = True,
        produces_output: bool = True,
    ) -> dict[str, Any]:
        """POST once, retrying the cheap transient failures, booking every attempt."""
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                with ledger.from_call_site():
                    return await self._attempt(payload, op, path, stream, produces_output)
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

    async def _attempt(
        self,
        payload: dict[str, Any],
        op: str,
        path: str,
        stream: bool,
        produces_output: bool,
    ) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        # include_usage is what keeps a streamed call metered: the counts arrive on one
        # final chunk with no choices, and only when this is asked for.
        # Chat calls only: an embeddings request has nothing to stream, and the endpoint
        # would refuse the parameters.
        if stream:
            payload = {**payload, "stream": True, "stream_options": {"include_usage": True}}
        # Monotonic, not wall clock: this becomes the cost of a locally served call, and
        # a clock adjustment mid-request would otherwise price the turn as negative.
        started = time.monotonic()
        # Set once, by the stream reader, when the first content or tool-call fragment
        # arrives. A list rather than a variable so the reader can set it, and so a stream
        # that fails halfway still books the time its first fragment came.
        first_output: list[float] = []

        def mark_first_output() -> None:
            if not first_output:
                first_output.append(time.monotonic())

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
                first_token_ms=(int((first_output[0] - started) * 1000) if first_output else None),
                status=status,
                error=error,
                priced_as=self._priced_as,
                request=_request_of(payload),
            )

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                async with client.stream(
                    "POST",
                    f"{self._base_url}{path}",
                    json=payload,
                    headers=headers,
                ) as response:
                    status = response.status_code
                    if status >= 400:
                        said = (await response.aread()).decode(errors="replace")
                        logger.error("llm tier returned %s: %s", status, said[:200])
                        book(status, None, said[:200])
                        error = LLMError(f"LLM tier rejected the request ({status}): {said[:200]}")
                        if status in _RETRYABLE_STATUSES:
                            raise _Transient(error)
                        raise error

                    def fail(reason: str) -> None:
                        book(status, None, reason)

                    if "text/event-stream" in response.headers.get("content-type", ""):
                        body = await _assemble_stream(response, mark_first_output, fail)
                    else:
                        # A server that ignored stream: true and answered in one piece.
                        # Still a valid answer; it just has no first-token time to give.
                        raw = (await response.aread()).decode(errors="replace")
                        body = _one_piece(raw, fail)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.RemoteProtocolError) as exc:
            # Nothing connected, or the server hung up mid-response (which a stream makes
            # more likely, since the connection is held for the whole answer): cheap to
            # retry and usually passing.
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
        # Logged after parsing so the token usage is in reach: any tier can serve any
        # live turn, and until now those tokens were spent with no record at all. One format
        # across tiers means one grep finds every tier's spend.
        #
        # `.get` is not a no-fallbacks shrug here: usage is optional provider metadata that
        # is recorded and never acted on, unlike the required data ARCHITECTURE.md 4 is
        # about. A tier that omits it, or a stream cut before its usage chunk, logs
        # usage=None, which is the honest answer.
        logger.info(
            "llm tier call model=%s status=%s usage=%s", self._model, status, body.get("usage")
        )
        # The durable half of the same fact. The log line is for reading now; this is for
        # answering "what did that survey cost, on which model" months from now, when the
        # logs have rotated away.
        usage = body.get("usage")
        # An embeddings response reports prompt tokens only, because it makes no output.
        # Zero output is a fact about the endpoint, not a missing figure, so it is booked as
        # zero and the call is priced, rather than counted as unmetered for ever.
        if not produces_output and isinstance(usage, dict) and "completion_tokens" not in usage:
            usage = {**usage, "completion_tokens": 0}
        book(status, usage, None)
        return body

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

    def _system_message(self, system: str) -> dict[str, Any]:
        """The system message, marked cacheable when the tier opted in.

        The system prompt is the large, stable prefix every turn shares, so it is the
        natural cache breakpoint: a caching-capable provider reuses it instead of
        re-pricing it per turn. The annotation is omitted unless `prompt_cache` is set,
        because providers that do not understand it (notably OpenAI) answer a 400.
        """
        message: dict[str, Any] = {"role": "system", "content": system}
        if self._prompt_cache:
            message["cache_control"] = {"type": "ephemeral"}
        return message

    def _check_context_window(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        max_tokens: int,
    ) -> None:
        """Refuse a prompt that would not fit this tier's stated context, before it is sent.

        No tokenizer is vendored here for the same reason no provider SDK is: four tiers
        can mean four different tokenizers, and getting one exactly right would not make
        the other three correct. The estimate below (~4 characters per token, the usual
        rule of thumb for English) is a bound to catch the case that actually happens —
        several long_text answers pushing a small local tier past its window — not a
        precise accounting, and it is never allowed to invent a limit: a tier that has not
        stated `context_window` is not checked at all: unstated stays unstated, never 0.
        """
        if self._context_window is None:
            return
        text = system + "".join(m.get("content", "") for m in messages) + json.dumps(tools)
        estimated_prompt_tokens = max(1, len(text) // 4)
        if estimated_prompt_tokens + max_tokens > self._context_window:
            raise ContextWindowExceededError(
                f"Tier {self._tier} ({self._model}) is configured for a "
                f"{self._context_window}-token context, but this prompt is an estimated "
                f"{estimated_prompt_tokens} tokens plus {max_tokens} reserved for the reply "
                f"({estimated_prompt_tokens + max_tokens} total). Refused before sending "
                "rather than left for the provider to reject."
            )

    async def tool_call(
        self,
        *,
        system: str,
        prompt: str,
        tool_name: str,
        tool_description: str,
        input_schema: dict[str, Any],
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        max_tokens = max_tokens or self._max_completion_tokens
        tools = self._as_openai_tools(
            [{"name": tool_name, "description": tool_description, "input_schema": input_schema}]
        )
        self._check_context_window(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            tools=tools,
            max_tokens=max_tokens,
        )
        payload = {
            "model": self._model,
            # "max_completion_tokens", not "max_tokens". The gpt-5 and o-series models
            # reject the older name with a 400 rather than ignoring it, which would take
            # tier 1 out of the chain silently and leave every call served by tier 2.
            # Groq and OpenRouter both accept this spelling, so it is the one name every
            # tier answers to; checked against all three on 12 Aug 2026.
            "max_completion_tokens": max_tokens,
            "messages": [
                self._system_message(system),
                {"role": "user", "content": prompt},
            ],
            "tools": tools,
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
        max_tokens: int | None = None,
        # Accepted and ignored: one tier has nothing to cascade to, so the flag can only
        # mean something to FailoverLLM. It is on the protocol because callers are typed
        # against the protocol and cannot tell which of the two they hold.
        cascade_on_no_tool_call: bool = True,
    ) -> ToolTurn:
        max_tokens = max_tokens or self._max_completion_tokens
        openai_tools = self._as_openai_tools(tools)
        self._check_context_window(
            system=system, messages=messages, tools=openai_tools, max_tokens=max_tokens
        )
        payload = {
            "model": self._model,
            # The newer spelling, for the reason given in tool_call above.
            "max_completion_tokens": max_tokens,
            "messages": [self._system_message(system), *messages],
            "tools": openai_tools,
            # "required" alone means at least one call, not exactly one. The second half
            # of "exactly" is parallel_tool_calls, and the belt for endpoints that
            # ignore it is _first_tool_call refusing multi-call answers.
            "tool_choice": "required",
            "parallel_tool_calls": False,
        }
        data = await self._post(payload, op="tool_turn")
        name, arguments, said = self._first_tool_call(data)
        return ToolTurn(text=said.strip(), tool_name=name, tool_input=arguments)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """One vector per text, in the order given, from the embeddings endpoint.

        Every item is shape-checked, and the vectors are placed by the index the provider
        returns rather than by position, which the API does not promise. A count or index
        that does not line up with the input fails loudly: a vector attached to the wrong
        text is a silent wrong answer to every similarity question after it.
        """
        if not texts:
            return []
        body = await self._post(
            {"model": self._model, "input": texts},
            op="embed",
            path="/embeddings",
            stream=False,
            produces_output=False,
        )
        items = body.get("data")
        if not isinstance(items, list) or len(items) != len(texts):
            raise LLMError(
                f"Embeddings endpoint returned {len(items) if isinstance(items, list) else 'no'} "
                f"vectors for {len(texts)} texts."
            )
        vectors: list[list[float] | None] = [None] * len(texts)
        for item in items:
            index = item.get("index") if isinstance(item, dict) else None
            vector = item.get("embedding") if isinstance(item, dict) else None
            if (
                not isinstance(index, int)
                or not 0 <= index < len(texts)
                or vectors[index] is not None
            ):
                raise LLMError(f"Embeddings endpoint returned a bad or repeated index: {index!r}.")
            if (
                not isinstance(vector, list)
                or not vector
                or not all(isinstance(x, int | float) for x in vector)
            ):
                raise LLMError("Embeddings endpoint returned a malformed vector.")
            vectors[index] = [float(x) for x in vector]
        return [v for v in vectors if v is not None]
