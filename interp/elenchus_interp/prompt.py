"""Render a captured request the way Qwen reads it, and name the part every token came from."""

from dataclasses import dataclass
from typing import Any, Literal

TEMPLATE = "template"


class PromptLayoutError(ValueError):
    """The rendered prompt does not contain a part it should: the template changed shape."""


@dataclass(frozen=True)
class SectionSpan:
    key: str
    label: str
    kind: Literal["system", "tools", "message"]
    role: str | None
    char_start: int
    char_end: int


@dataclass(frozen=True)
class Rendered:
    text: str
    ids: list[int]
    # For every token, the key of the section its first character falls in.
    token_sections: list[str]
    sections: list[SectionSpan]


def _content(message: dict[str, Any], index: int) -> str:
    content = message.get("content")
    if not isinstance(content, str):
        raise PromptLayoutError(f"message {index} has no text content to read")
    return content


def render(tokenizer: Any, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Rendered:
    """The prompt as the chat template writes it, with thinking off, split into sections.

    Thinking is off because the conduct call asks for a tool, not a chain of reasoning, and
    a reading taken mid-thought would describe a different moment. Each message is found by
    its text in the rendered prompt, in order, so a template that rewrites a message fails
    loudly here rather than attributing its tokens to the wrong part.
    """
    text: str = tokenizer.apply_chat_template(
        messages, tools=tools, add_generation_prompt=True, tokenize=False, enable_thinking=False
    )
    spans: list[SectionSpan] = []
    cursor = 0
    counts: dict[str, int] = {}
    for index, message in enumerate(messages):
        role = str(message.get("role"))
        content = _content(message, index).strip()
        if not content:
            continue
        at = text.find(content, cursor)
        if at < 0:
            raise PromptLayoutError(f"message {index} ({role}) is not in the rendered prompt")
        if role == "system" and index == 0:
            spans.append(
                SectionSpan("system", "System prompt", "system", role, at, at + len(content))
            )
        else:
            counts[role] = counts.get(role, 0) + 1
            spans.append(
                SectionSpan(
                    f"message-{index}",
                    f"{role.capitalize()} message {counts[role]}",
                    "message",
                    role,
                    at,
                    at + len(content),
                )
            )
        cursor = at + len(content)
        if index == 0 and role == "system":
            # Qwen's template writes the tool definitions into the system turn, after it.
            start = text.find("# Tools", cursor)
            end = text.find("<|im_end|>", start)
            if start < 0 or end < 0:
                raise PromptLayoutError("the tool definitions are not in the rendered system turn")
            spans.append(SectionSpan("tools", "Tool definitions", "tools", None, start, end))
            cursor = end
    if not any(span.kind == "tools" for span in spans):
        raise PromptLayoutError("the prompt has no system message to carry the tool definitions")

    encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    ids: list[int] = list(encoded["input_ids"])
    token_sections = []
    for start, _end in encoded["offset_mapping"]:
        owner = next((s.key for s in spans if s.char_start <= start < s.char_end), TEMPLATE)
        token_sections.append(owner)
    return Rendered(text=text, ids=ids, token_sections=token_sections, sections=spans)
