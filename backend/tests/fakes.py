"""Test doubles for the LLM, substituted at the client wrapper's boundary.

Every test runs without an API key because nothing below this line talks to Anthropic.
"""

from typing import Any

from app.llm.client import ToolTurn


class FakeLLM:
    """Replays scripted turns and records which tools the engine offered each time."""

    def __init__(self, *turns: ToolTurn) -> None:
        self._turns = list(turns)
        self.calls = 0
        self.offered: list[list[str]] = []
        self.briefings: list[str] = []

    async def tool_turn(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
        max_tokens: int = 1024,
    ) -> ToolTurn:
        self.offered.append([t["name"] for t in tools])
        self.briefings.append(system)
        if not self._turns:
            raise AssertionError("engine asked for a turn the test did not script")
        turn = self._turns[min(self.calls, len(self._turns) - 1)]
        self.calls += 1
        return turn

    async def tool_call(self, **_: Any) -> dict[str, Any]:
        raise AssertionError("the conduct engine must not use one-shot tool_call")


def record(value: Any, say: str = "Thanks.") -> ToolTurn:
    return ToolTurn(text=say, tool_name="record_answer", tool_input={"value": value})


def follow_up(text: str) -> ToolTurn:
    return ToolTurn(text="", tool_name="ask_follow_up", tool_input={"follow_up_text": text})


def move_on(say: str = "Next question.") -> ToolTurn:
    return ToolTurn(text=say, tool_name="move_on", tool_input={})
