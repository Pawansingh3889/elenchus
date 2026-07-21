"""The single Anthropic client wrapper.

It owns the model id, API key, retries, and token logging. Nothing else imports the
anthropic SDK. Callers get schema-constrained tool calls back as raw input dicts to
validate — the engine, not this module, decides what to do with them.
"""

import logging
from dataclasses import dataclass
from typing import Any, Protocol, cast

import anthropic
from anthropic.types import TextBlock, ToolUseBlock

from app.config import get_settings
from app.errors import AppError

logger = logging.getLogger("app.llm")


class LLMError(AppError):
    status_code = 502
    code = "llm_error"


@dataclass(frozen=True)
class ToolTurn:
    """One model turn: what it said, and the single tool it chose."""

    text: str
    tool_name: str
    tool_input: dict[str, Any]


class LLMProtocol(Protocol):
    """The surface the engines depend on. Tests substitute a fake at this boundary."""

    async def tool_call(
        self,
        *,
        system: str,
        prompt: str,
        tool_name: str,
        tool_description: str,
        input_schema: dict[str, Any],
        max_tokens: int = ...,
    ) -> dict[str, Any]: ...

    async def tool_turn(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        max_tokens: int = ...,
    ) -> ToolTurn: ...


class LLMClient:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise LLMError("ANTHROPIC_API_KEY is not configured.")
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key, max_retries=2)
        self._model = settings.anthropic_model

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
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            tools=[
                {
                    "name": tool_name,
                    "description": tool_description,
                    "input_schema": input_schema,
                }
            ],
            tool_choice={"type": "tool", "name": tool_name},
        )
        logger.info("llm tool_call model=%s usage=%s", self._model, response.usage)
        for block in response.content:
            if isinstance(block, ToolUseBlock) and block.name == tool_name:
                return cast("dict[str, Any]", block.input)
        raise LLMError("Model did not return the expected tool call.")

    async def tool_turn(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        max_tokens: int = 1024,
    ) -> ToolTurn:
        """Force exactly one tool from ``tools`` and return it with any spoken text."""
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=cast("Any", messages),
            tools=cast("Any", tools),
            tool_choice={"type": "any"},
        )
        logger.info("llm tool_turn model=%s usage=%s", self._model, response.usage)
        said: list[str] = []
        name: str | None = None
        payload: dict[str, Any] = {}
        for block in response.content:
            if isinstance(block, TextBlock):
                said.append(block.text)
            elif isinstance(block, ToolUseBlock):
                name = block.name
                payload = cast("dict[str, Any]", block.input)
        if name is None:
            raise LLMError("Model returned no tool call.")
        return ToolTurn(text="\n".join(said).strip(), tool_name=name, tool_input=payload)
