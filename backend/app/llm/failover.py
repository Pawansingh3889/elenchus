"""Provider failover: try the primary LLM, fall back to the backup on a typed failure.

The primary (Anthropic) stays the default so quality-sensitive flows use the better model
whenever it is available; the backup is reached only when the primary actually raises an
``LLMError`` (transport down, rate limited, credit exhausted, malformed tool call). If the
backup also fails, its ``LLMError`` propagates — the system still fails loudly, never
silently degrading.
"""

import logging
from typing import Any

from app.llm.client import LLMError, LLMProtocol, ToolTurn

logger = logging.getLogger("app.llm.failover")


class FailoverLLM:
    """Wrap two ``LLMProtocol`` clients as primary and backup."""

    def __init__(self, primary: LLMProtocol, backup: LLMProtocol) -> None:
        self._primary = primary
        self._backup = backup

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
        try:
            return await self._primary.tool_call(
                system=system,
                prompt=prompt,
                tool_name=tool_name,
                tool_description=tool_description,
                input_schema=input_schema,
                max_tokens=max_tokens,
            )
        except LLMError as exc:
            logger.warning("primary LLM failed on tool_call, using backup: %s", exc)
            return await self._backup.tool_call(
                system=system,
                prompt=prompt,
                tool_name=tool_name,
                tool_description=tool_description,
                input_schema=input_schema,
                max_tokens=max_tokens,
            )

    async def tool_turn(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        max_tokens: int = 1024,
    ) -> ToolTurn:
        try:
            return await self._primary.tool_turn(
                system=system, messages=messages, tools=tools, max_tokens=max_tokens
            )
        except LLMError as exc:
            logger.warning("primary LLM failed on tool_turn, using backup: %s", exc)
            return await self._backup.tool_turn(
                system=system, messages=messages, tools=tools, max_tokens=max_tokens
            )
