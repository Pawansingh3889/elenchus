"""Every token of a rendered prompt belongs to exactly the part it came from."""

import pytest

from elenchus_interp.prompt import TEMPLATE, PromptLayoutError, render


def test_each_message_and_the_tools_become_sections_in_order(tokenizer, captured):
    rendered = render(tokenizer, captured["messages"], captured["tools"])
    assert [s.key for s in rendered.sections] == ["system", "tools", "message-1", "message-2"]
    assert len(rendered.token_sections) == len(rendered.ids)
    for span in rendered.sections:
        assert rendered.text[span.char_start : span.char_end].strip()
    said = next(s for s in rendered.sections if s.key == "message-2")
    assert rendered.text[said.char_start : said.char_end] == captured["messages"][2]["content"]
    # The tool names are read inside the tools section, not the template's.
    assert (
        '"record_answer"'
        in rendered.text[rendered.sections[1].char_start : rendered.sections[1].char_end]
    )


def test_thinking_is_off_and_the_template_owns_its_own_tokens(tokenizer, captured):
    rendered = render(tokenizer, captured["messages"], captured["tools"])
    assert rendered.text.rstrip().endswith("</think>")
    assert rendered.token_sections[0] == TEMPLATE
    assert set(rendered.token_sections) == {"system", "tools", "message-1", "message-2", TEMPLATE}


def test_a_request_without_a_system_turn_fails_loudly(tokenizer, captured):
    with pytest.raises(PromptLayoutError, match="no system message"):
        render(tokenizer, captured["messages"][1:], captured["tools"])
