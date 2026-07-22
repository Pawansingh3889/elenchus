"""Generation tests with the LLM mocked at the client boundary (no API key needed)."""

from typing import Any

import pytest

from app.llm.client import LLMError
from app.templates.enums import TemplateStatus
from app.templates.generation import GenerationService


class FakeLLM:
    """Returns canned tool payloads in order; repeats the last one thereafter."""

    def __init__(self, *payloads: dict[str, Any]) -> None:
        self._payloads = list(payloads)
        self.calls = 0

    async def tool_call(self, **_: Any) -> dict[str, Any]:
        payload = self._payloads[min(self.calls, len(self._payloads) - 1)]
        self.calls += 1
        return payload


_VALID: dict[str, Any] = {
    "title": "Onboarding",
    "description": "New starter survey",
    "questions": [
        {"text": "Your role?", "answer_type": "short_text"},
        {"text": "Systems used?", "answer_type": "multi_select", "options": ["ERP", "BI"]},
    ],
}
# A single-select with no options is schema-valid but fails our business validation.
_INVALID: dict[str, Any] = {
    "title": "X",
    "questions": [{"text": "q", "answer_type": "single_select"}],
}


async def test_generate_persists_valid_draft(session, author):
    fake = FakeLLM(_VALID)
    template = await GenerationService(session, llm=fake).generate_draft("onboarding", author)
    assert fake.calls == 1
    assert template.title == "Onboarding"
    assert template.status is TemplateStatus.draft
    assert [q.text for q in template.questions] == ["Your role?", "Systems used?"]


async def test_catch_all_options_become_a_write_in(session, author):
    """A live run recorded `{'option': 'Other'}` and lost the respondent's actual team."""
    fake = FakeLLM(
        {
            "title": "Onboarding",
            "questions": [
                {
                    "text": "Which team?",
                    "answer_type": "single_select",
                    "options": ["Sales", "Engineering", "Other"],
                },
                {
                    "text": "Which tools?",
                    "answer_type": "multi_select",
                    "options": ["ERP", "BI", "None of the above", "Prefer not to say"],
                },
                {
                    "text": "Which site?",
                    "answer_type": "single_select",
                    "options": ["Hull", "Leeds"],
                },
            ],
        }
    )
    template = await GenerationService(session, llm=fake).generate_draft("teams", author)

    team, tools, site = template.questions
    assert (team.options, team.allow_other) == (["Sales", "Engineering"], True)
    assert (tools.options, tools.allow_other) == (["ERP", "BI"], True)
    # Untouched: nothing to strip, so no write-in is silently opened up.
    assert (site.options, site.allow_other) == (["Hull", "Leeds"], False)


async def test_generate_retries_once_then_succeeds(session, author):
    fake = FakeLLM(_INVALID, _VALID)
    template = await GenerationService(session, llm=fake).generate_draft("x", author)
    assert fake.calls == 2
    assert template.title == "Onboarding"


async def test_generate_fails_loudly_after_retry(session, author):
    fake = FakeLLM(_INVALID, _INVALID)
    with pytest.raises(LLMError):
        await GenerationService(session, llm=fake).generate_draft("x", author)
    assert fake.calls == 2
