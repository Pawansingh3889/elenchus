"""A backup LLM client speaking the OpenAI Chat Completions API.

The primary client (``app.llm.client.LLMClient``) talks to Anthropic. This one talks to
any OpenAI-compatible server — vLLM, NVIDIA NIM, OpenRouter, Ollama, and similar — so a
model such as Nemotron/Hermes can stand in when the primary is unavailable.

It implements the same ``LLMProtocol`` surface and returns the same validated shapes, so
the conduct engine and generation service cannot tell which provider answered. As with the
primary, SDK/transport failures become one typed ``LLMError`` and a malformed or missing
tool call fails loudly rather than degrading.
"""

import json
import logging
import re
from typing import Any, cast

import httpx

from app.llm.client import LLMError, NoToolCallError, ToolTurn

logger = logging.getLogger("app.llm.backup")


def _balanced_object(text: str) -> str | None:
    """The first balanced top-level {...} in the text, or None.

    Brace-counting with string awareness — enough to lift one JSON object out of
    surrounding prose without a full parser.
    """
    start = text.find("{")
    if start == -1:
        return None
    depth, in_string, escaped = 0, False, False
    for index in range(start, len(text)):
        char = text[index]
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
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


# A local CPU-served model (the very case the backup exists for) can legitimately take
# well over a minute on a cold load or a long survey, so the read timeout is generous
# and configurable (LLM_BACKUP_TIMEOUT_SECONDS). Connecting, by contrast, should be
# near-instant — a short connect timeout keeps a *genuinely* unreachable endpoint from
# stalling a request for the full read window.
DEFAULT_TIMEOUT_SECONDS = 120.0
CONNECT_TIMEOUT_SECONDS = 10.0


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
    ) -> None:
        if not base_url or not model:
            raise LLMError("Backup LLM is enabled but base_url/model are not configured.")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = httpx.Timeout(timeout_seconds, connect=CONNECT_TIMEOUT_SECONDS)
        self._transport = transport  # injectable so tests need no network

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions", json=payload, headers=headers
                )
        except httpx.TimeoutException as exc:
            # str(ReadTimeout) is usually empty, which once surfaced as a blank
            # "could not reach" while the model was merely slow — name the failure.
            logger.error("backup llm timed out: %r", exc)
            raise LLMError(
                f"Backup LLM timed out after {self._timeout.read}s — the model may be "
                "loading or too slow for the configured LLM_BACKUP_TIMEOUT_SECONDS."
            ) from exc
        except httpx.HTTPError as exc:
            # repr, not str: several httpx errors stringify to "".
            logger.error("backup llm call failed: %r", exc)
            raise LLMError(f"Could not reach the backup LLM: {exc!r}") from exc
        if response.status_code >= 400:
            logger.error("backup llm returned %s: %s", response.status_code, response.text[:200])
            raise LLMError(
                f"Backup LLM rejected the request ({response.status_code}): {response.text[:200]}"
            )
        logger.info("llm backup call model=%s status=%s", self._model, response.status_code)
        return cast("dict[str, Any]", response.json())

    @staticmethod
    def _salvage_from_content(said: Any) -> list[dict[str, Any]]:
        """Local models often write the tool call INTO the text instead of tool_calls.

        Recover a tool-call-shaped JSON object ({"name": ..., "arguments"/"parameters":
        {...}}) from the content: the whole text, a fenced ``` block, or a single JSON
        object embedded in prose ("Sure! {...}"). Anything that does not yield exactly
        that shape stays a hard failure.
        """
        if not isinstance(said, str):
            return []
        text = said.strip()

        candidates = [text]
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
        if fence:
            candidates.append(fence.group(1))
        embedded = _balanced_object(text)
        if embedded:
            candidates.append(embedded)

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
        """Pull (tool name, parsed arguments, spoken text) from the first choice."""
        choices = data.get("choices") or []
        if not choices:
            raise LLMError("Backup LLM returned no choices.")
        message = choices[0].get("message") or {}
        said = message.get("content")
        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            tool_calls = OpenAICompatibleLLMClient._salvage_from_content(said)
            if tool_calls:
                said = ""  # the content WAS the tool call; there is nothing spoken
        if not tool_calls:
            raise NoToolCallError("Backup LLM returned no tool call.")
        function = tool_calls[0].get("function") or {}
        name = function.get("name")
        if not isinstance(name, str):
            raise LLMError("Backup LLM tool call is missing a name.")
        raw_arguments = function.get("arguments", "{}")
        try:
            arguments = (
                json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
            )
        except json.JSONDecodeError as exc:
            raise LLMError(f"Backup LLM tool arguments were not valid JSON: {exc}") from exc
        if not isinstance(arguments, dict):
            raise LLMError("Backup LLM tool arguments were not a JSON object.")
        return name, cast("dict[str, Any]", arguments), said if isinstance(said, str) else ""

    @staticmethod
    def _as_openai_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Translate Anthropic-style tools (name/description/input_schema) to OpenAI's shape."""
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
        }
        data = await self._post(payload)
        name, arguments, _ = self._first_tool_call(data)
        if name != tool_name:
            raise LLMError(f"Backup LLM called {name!r}, expected {tool_name!r}.")
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
            "tool_choice": "required",  # force exactly one tool; the model picks which
        }
        data = await self._post(payload)
        name, arguments, said = self._first_tool_call(data)
        return ToolTurn(text=said.strip(), tool_name=name, tool_input=arguments)
