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


class EmbeddingsNotConfiguredError(AppError):
    """Something asked for embeddings on a deployment that has none. 503: nothing retries
    its way out of a missing setting, but the service is otherwise up."""

    status_code = 503
    code = "embeddings_not_configured"


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


class ContextWindowExceededError(LLMError):
    """The outgoing prompt would not fit this tier's configured context window.

    Caught before the request leaves, not learned from a provider's 400: a run with
    several long_text answers against a small tier can overflow a local model's context
    long before TRANSCRIPT_WINDOW's message count says anything is wrong. A plain
    ``LLMError``, deliberately, so ``FailoverLLM`` treats it like any other tier failure
    and falls through to the next tier, which may simply have more room.

    Only raised when the tier states a context window at all: an unstated one means the
    check has nothing to check against, not that the prompt is assumed to fit.
    """

    code = "llm_context_window_exceeded"


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
        max_tokens: int | None = None,
    ) -> dict[str, Any]: ...

    async def tool_turn(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        max_tokens: int | None = None,
        cascade_on_no_tool_call: bool = ...,
    ) -> ToolTurn: ...


class EmbedderProtocol(Protocol):
    """One vector per text, in the order given. Tests substitute a fake at this boundary."""

    @property
    def model(self) -> str: ...

    async def embed(self, texts: list[str]) -> list[list[float]]: ...
