"""Provider failover: try each LLM in an ordered chain until one answers.

The chain runs in tier order, lowest first: OpenAI, then Groq, then OpenRouter, then a
local Ollama. A tier is reached only when every tier before it raises an ``LLMError``
(transport down, rate limited, credit exhausted, malformed tool call). If every tier
fails, the last error propagates: the system still fails loudly, never silently
degrading.

One carve-out on the conversational path, and it is the caller's to ask for:
``cascade_on_no_tool_call=False`` makes ``NoToolCallError`` propagate without touching
the next tier, because a model that merely chatted is not a downed provider. Only a
caller that answers that error with a retry of its own may ask for it. The default
cascades, since a caller with no retry has nothing else to fall back on.

``FailoverLLM`` itself satisfies ``LLMProtocol``, so callers can't tell a chain from a
single client.
"""

import logging
from typing import Any

from app.llm.client import LLMError, LLMProtocol, NoToolCallError, ToolTurn

logger = logging.getLogger("app.llm.failover")


class FailoverLLM:
    """Chain two or more ``LLMProtocol`` clients as tiers, tried in order."""

    def __init__(self, *clients: LLMProtocol) -> None:
        if not clients:
            raise ValueError("FailoverLLM needs at least one client")
        self._clients = clients

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
        errors: list[LLMError] = []
        for tier, client in enumerate(self._clients, start=1):
            try:
                return await client.tool_call(
                    system=system,
                    prompt=prompt,
                    tool_name=tool_name,
                    tool_description=tool_description,
                    input_schema=input_schema,
                    max_tokens=max_tokens,
                )
            except LLMError as exc:
                self._note(tier, "tool_call", exc)
                errors.append(exc)
        raise errors[-1]

    async def tool_turn(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        max_tokens: int = 1024,
        cascade_on_no_tool_call: bool = True,
    ) -> ToolTurn:
        errors: list[LLMError] = []
        for tier, client in enumerate(self._clients, start=1):
            try:
                return await client.tool_turn(
                    system=system,
                    messages=messages,
                    tools=tools,
                    max_tokens=max_tokens,
                    cascade_on_no_tool_call=cascade_on_no_tool_call,
                )
            except NoToolCallError as exc:
                # The model chatted, or called two tools at once: responsive, not down.
                # Only a caller that retries the error itself gains from stopping here,
                # and it gains a lot, since dropping to ever weaker tiers while the
                # healthy one was fine then re-runs the whole cascade when the nudge
                # fires. A caller without that retry must still cascade: making this
                # unconditional took failover away from template drafting and run
                # summarising, which have no nudge, and turned one chatty turn from
                # those into an immediate 503 with three healthy tiers left untried.
                if not cascade_on_no_tool_call:
                    raise
                self._note(tier, "tool_turn", exc)
                errors.append(exc)
            except LLMError as exc:
                self._note(tier, "tool_turn", exc)
                errors.append(exc)
        raise errors[-1]

    def _note(self, tier: int, op: str, exc: LLMError) -> None:
        count = len(self._clients)
        if tier < count:
            logger.warning("LLM tier %d/%d failed on %s, trying next: %s", tier, count, op, exc)
        else:
            logger.warning("LLM tier %d/%d (last) failed on %s: %s", tier, count, op, exc)
