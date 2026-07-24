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
from typing import Any, cast

import httpx

from app.llm.client import LLMError, ToolTurn

logger = logging.getLogger("app.llm.backup")

TIMEOUT_SECONDS = 60.0


class OpenAICompatibleLLMClient:
    """Force one schema-constrained tool call out of an OpenAI-compatible endpoint."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not base_url or not model:
            raise LLMError("Backup LLM is enabled but base_url/model are not configured.")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._transport = transport  # injectable so tests need no network

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        try:
            async with httpx.AsyncClient(
                timeout=TIMEOUT_SECONDS, transport=self._transport
            ) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions", json=payload, headers=headers
                )
        except httpx.HTTPError as exc:
            logger.error("backup llm call failed: %s", exc)
            raise LLMError(f"Could not reach the backup LLM: {exc}") from exc
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

        When the content is exactly one JSON object shaped like a tool call
        ({"name": ..., "arguments"/"parameters": {...}}), recover it; anything less
        unambiguous stays a hard failure.
        """
        if not isinstance(said, str):
            return []
        text = said.strip()
        if not (text.startswith("{") and text.endswith("}")):
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return []
        if not isinstance(parsed, dict) or not isinstance(parsed.get("name"), str):
            return []
        arguments = parsed.get("arguments", parsed.get("parameters", {}))
        if not isinstance(arguments, dict):
            return []
        return [{"function": {"name": parsed["name"], "arguments": json.dumps(arguments)}}]

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
            raise LLMError("Backup LLM returned no tool call.")
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
