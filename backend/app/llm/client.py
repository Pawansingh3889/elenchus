"""The contract every LLM client satisfies: typed errors, one turn shape, one protocol.

No provider SDK is imported here. The concrete client lives in ``openai_compatible``
and speaks the OpenAI Chat Completions API, which is what every configured tier answers.
Callers get schema-constrained tool calls back as raw input dicts to validate, and the
engine, not this module, decides what to do with them.
"""

from dataclasses import dataclass
from typing import Any, Protocol

from app.errors import AppError


class LLMError(AppError):
    status_code = 502
    code = "llm_error"


class NoToolCallError(LLMError):
    """The model did not produce exactly one tool call: none at all, or several at once.

    Distinguished from other LLM failures because it is cheaply retryable: the model is
    responsive, it just went off-script. Whether the failover chain treats it as a downed
    tier is the caller's to say, via ``cascade_on_no_tool_call`` below, because only the
    caller knows whether it will retry. Timeouts and transport errors stay plain LLMError
    so a retry never doubles a 120-second wait.
    """

    code = "llm_no_tool_call"


class TruncatedTurnError(LLMError):
    """The turn hit max_tokens before the model chose a tool.

    Deliberately NOT a NoToolCallError: the engine retries those with a nudge, and a
    retry at the same token budget truncates in exactly the same place. Failing over to
    another provider (or raising) beats spending a turn to learn nothing.
    """

    code = "llm_truncated_turn"


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
        # Whether a NoToolCallError should drop the turn to the next tier. Defaults to
        # cascading, because that is the only recovery a caller without a retry of its
        # own has; a caller that answers the error with a nudged retry passes False so
        # its healthy tier is not abandoned. On the protocol rather than on FailoverLLM
        # because callers cannot tell a chain from a single client, which is the point.
        cascade_on_no_tool_call: bool = ...,
    ) -> ToolTurn: ...
