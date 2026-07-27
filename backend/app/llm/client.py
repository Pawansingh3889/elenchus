"""The single Anthropic client wrapper.

It owns the model id, API key, retries, and token logging. Nothing else imports the
anthropic SDK. Callers get schema-constrained tool calls back as raw input dicts to
validate — the engine, not this module, decides what to do with them.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Protocol, cast

import anthropic
from anthropic.types import TextBlock, ToolUseBlock

from app.config import get_settings
from app.errors import AppError

logger = logging.getLogger("app.llm")

# A survey turn that has not come back inside a minute is not coming back usefully;
# without this the SDK would sit on its own multi-minute default and hold a worker.
TIMEOUT_SECONDS = 60.0


class LLMError(AppError):
    status_code = 502
    code = "llm_error"


class NoToolCallError(LLMError):
    """The model produced a turn with no tool call at all.

    Distinguished from other LLM failures because it is cheaply retryable: the model is
    responsive, it just chatted instead of acting. Timeouts and transport errors stay
    plain LLMError so a retry never doubles a 120-second wait.
    """

    code = "llm_no_tool_call"


class TruncatedTurnError(LLMError):
    """The turn hit max_tokens before the model chose a tool.

    Deliberately NOT a NoToolCallError: the engine retries those with a nudge, and a
    retry at the same token budget truncates in exactly the same place. Failing over to
    another provider (or raising) beats spending a turn to learn nothing.
    """

    code = "llm_truncated_turn"


@asynccontextmanager
async def _api_errors() -> AsyncIterator[None]:
    """Map SDK failures to one typed error, so callers never see a raw 500."""
    try:
        yield
    except anthropic.APIStatusError as exc:
        logger.error("anthropic returned %s: %s", exc.status_code, exc.message)
        raise LLMError(
            f"Anthropic rejected the request ({exc.status_code}): {_detail(exc)}"
        ) from exc
    except anthropic.APIError as exc:
        logger.error("anthropic call failed: %s", exc)
        raise LLMError(f"Could not reach the Anthropic API: {exc}") from exc


def _detail(exc: anthropic.APIStatusError) -> str:
    body = exc.body
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str):
                return message
    return exc.message


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
        self._client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key, max_retries=2, timeout=TIMEOUT_SECONDS
        )
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
        async with _api_errors():
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
                tool_choice={
                    "type": "tool",
                    "name": tool_name,
                    "disable_parallel_tool_use": True,
                },
            )
        logger.info("llm tool_call model=%s usage=%s", self._model, response.usage)
        for block in response.content:
            if isinstance(block, ToolUseBlock) and block.name == tool_name:
                return cast("dict[str, Any]", block.input)
        if response.stop_reason == "max_tokens":
            raise TruncatedTurnError(
                f"Model hit the {max_tokens}-token limit before completing its tool call."
            )
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
        async with _api_errors():
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system,
                messages=cast("Any", messages),
                tools=cast("Any", tools),
                # Parallel tool use is on by default, and one turn carrying both
                # record_answer and move_on would have the engine act on whichever it
                # kept — dropping an answer the respondent actually gave. One tool per
                # turn is the engine's contract, so say so rather than pick a winner.
                tool_choice={"type": "any", "disable_parallel_tool_use": True},
            )
        logger.info("llm tool_turn model=%s usage=%s", self._model, response.usage)
        said: list[str] = []
        name: str | None = None
        payload: dict[str, Any] = {}
        for block in response.content:
            if isinstance(block, TextBlock):
                said.append(block.text)
            elif isinstance(block, ToolUseBlock) and name is None:
                # First tool wins if a model ignores the flag: it matches the backup
                # client, and the engine sees one action either way.
                name = block.name
                payload = cast("dict[str, Any]", block.input)
        if name is None:
            if response.stop_reason == "max_tokens":
                raise TruncatedTurnError(
                    f"Model hit the {max_tokens}-token limit before choosing a tool."
                )
            raise NoToolCallError("Model returned no tool call.")
        return ToolTurn(text="\n".join(said).strip(), tool_name=name, tool_input=payload)
