"""Prompt caching is opt-in per tier so OpenAI (which rejects `cache_control` with a
400) is never handed the annotation by default. These pin that the system message gains
the breakpoint only when the tier enabled it.
"""

from app.llm.openai_compatible import OpenAICompatibleLLMClient


def _client(prompt_cache: bool) -> OpenAICompatibleLLMClient:
    return OpenAICompatibleLLMClient(
        base_url="https://example.invalid/v1",
        api_key="x",
        model="m",
        prompt_cache=prompt_cache,
    )


def test_system_message_unmarked_when_cache_off() -> None:
    assert _client(False)._system_message("s") == {"role": "system", "content": "s"}


def test_system_message_marked_when_cache_on() -> None:
    assert _client(True)._system_message("s") == {
        "role": "system",
        "content": "s",
        "cache_control": {"type": "ephemeral"},
    }
