"""Test doubles for the LLM, substituted at the client wrapper's boundary.

Every test runs without an API key because nothing below this line reaches a provider.
"""

from typing import Any

from app.llm import ledger
from app.llm.client import LLMError, ToolTurn
from app.llm.openai_compatible import OpenAICompatibleLLMClient


class FakeLLM:
    """Replays scripted turns and records which tools the engine offered each time.

    A scripted entry may be an Exception instance instead of a ToolTurn, in which case
    that call raises it — for driving the engine's error-handling paths.

    ``serves_as`` makes the fake book a ledger row the way the real client does, naming
    the tier and model it is standing in for. Off by default, because most tests care
    about what the engine decided and not what it cost, and a fake that writes to the
    ledger file in every test would be writing to a file most of them never point
    anywhere. It is on for the tests about provenance, where the whole question is
    whether the engine reads back the tier that actually answered: without a booked row
    there is nothing to read, and the assertion would pass against None whether the
    engine looked or not.
    """

    def __init__(
        self, *turns: ToolTurn | Exception, serves_as: tuple[int, str] | None = None
    ) -> None:
        self._turns = list(turns)
        self._serves_as = serves_as
        self.calls = 0
        self.offered: list[list[str]] = []
        self.systems: list[str] = []
        self.briefings: list[str] = []
        self.messages_seen: list[list[dict[str, str]]] = []
        self.tools_seen: list[list[dict[str, Any]]] = []
        # Recorded so a test can assert who claimed the nudged retry, which decides
        # whether a chatty turn keeps its tier or falls to the next one.
        self.cascade_flags: list[bool] = []

    async def tool_turn(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        max_tokens: int = 1024,
        cascade_on_no_tool_call: bool = True,
    ) -> ToolTurn:
        self.offered.append([t["name"] for t in tools])
        self.systems.append(system)
        # The per-turn briefing rides in `messages` now, not `system` (engine.py's
        # cache-split: `system` is just prompt_file + language_note, stable across
        # turns so a caching tier can reuse it). `briefings` still means "everything
        # engine-authored the model was shown this turn", so it joins both rather than
        # assuming which exact message carries the state a test is asserting on.
        self.briefings.append("\n\n".join((system, *(m["content"] for m in messages))))
        self.messages_seen.append(messages)
        self.tools_seen.append(tools)
        self.cascade_flags.append(cascade_on_no_tool_call)
        if not self._turns:
            raise AssertionError("engine asked for a turn the test did not script")
        turn = self._turns[min(self.calls, len(self._turns) - 1)]
        self.calls += 1
        # The request the real client would send, in its shape, so the trace captures what
        # it captures in production: the system prompt first, tools as OpenAI functions.
        request = {
            "messages": [{"role": "system", "content": system}, *messages],
            "tools": OpenAICompatibleLLMClient._as_openai_tools(tools),
            "tool_choice": "required",
        }
        if isinstance(turn, Exception):
            self._book(status=0, error=repr(turn), request=request)
            raise turn
        self._book(status=200, error=None, request=request)
        return turn

    def _book(self, *, status: int, error: str | None, request: dict[str, Any]) -> None:
        """Book this call the way ``openai_compatible`` books a real one.

        Booked on the failure path too, and with ``error`` set, because that is the half
        that decides anything: a fake that only recorded its successes could never show
        that a tier which failed leaves the previous answer standing.
        """
        if self._serves_as is None:
            return
        tier, model = self._serves_as
        ledger.record(
            tier=tier,
            model=model,
            op="tool_turn",
            usage=None,
            latency_ms=0,
            status=status,
            error=error,
            request=request,
        )

    async def tool_call(self, **_: Any) -> dict[str, Any]:
        raise AssertionError("the conduct engine must not use one-shot tool_call")


def record(value: Any, say: str = "Thanks.") -> ToolTurn:
    return ToolTurn(text=say, tool_name="record_answer", tool_input={"value": value})


def follow_up(text: str, answer_so_far: Any = None) -> ToolTurn:
    """A probe. `answer_so_far` is what the reply already answered, banked before asking.

    Defaults to None, the "their reply held no answer to the question" case, because
    that is what every probe in these tests was written to mean. A test about banking
    passes a value; the engine ignores the field once a scripted answer exists.
    """
    return ToolTurn(
        text="",
        tool_name="ask_follow_up",
        tool_input={"follow_up_text": text, "answer_so_far": answer_so_far},
    )


def reply(text: str) -> ToolTurn:
    return ToolTurn(text="", tool_name="reply", tool_input={"reply_text": text})


def move_on(say: str = "Next question.") -> ToolTurn:
    return ToolTurn(text=say, tool_name="move_on", tool_input={})


class FakeEmbedder:
    """Embeddings by lookup; an unknown text gets a vector from its letter counts.

    Letter counts rather than zeros, so two different texts are never identical and the
    same text always is, which is all the cache and near-duplicate logic rely on.
    """

    model = "fake-embed"

    def __init__(self, vectors: dict[str, list[float]] | None = None, fail: bool = False) -> None:
        self.vectors = vectors or {}
        self.fail = fail
        self.calls: list[list[str]] = []

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        if self.fail:
            raise LLMError("embeddings down")
        return [self.vectors.get(t, _letters(t)) for t in texts]


def _letters(text: str) -> list[float]:
    counts = [0.0] * 27
    for ch in text.lower():
        counts[ord(ch) - 97 if "a" <= ch <= "z" else 26] += 1.0
    return counts
