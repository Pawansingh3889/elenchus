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


async def test_stringified_questions_are_decoded_before_validation(session, author):
    """Small backup models emit the right structure JSON-encoded into a string
    ('"questions": "[{...}]"'). That is a serialization slip, not bad content —
    decode it instead of burning the retry (a live run 502'd on exactly this)."""
    import json

    stringified = {
        "title": "Onboarding",
        "description": "",
        "questions": json.dumps(
            [
                {"text": "Your role?", "answer_type": "short_text"},
                {
                    "text": "Which shift?",
                    "answer_type": "single_select",
                    # the same slip one level down
                    "options": json.dumps(["Days", "Nights"]),
                },
            ]
        ),
    }
    fake = FakeLLM(stringified)
    template = await GenerationService(session, llm=fake).generate_draft("onboarding", author)

    assert fake.calls == 1  # repaired, not retried
    assert [q.text for q in template.questions] == ["Your role?", "Which shift?"]
    assert template.questions[1].options == ["Days", "Nights"]


async def test_almost_json_with_model_corruptions_is_still_decoded(session, author):
    """Two classic small-model corruptions of an otherwise-correct encoding must not
    defeat the repair: a literal newline inside a string value (invalid in strict
    JSON) and the Python-style \\' escape (never valid JSON). A live run failed on a
    stringified list that plain json.loads refused."""
    with_newline = '[{"text": "How often do you\nreview dashboards?", "answer_type": "short_text"}]'
    escaped_quote = (
        '[{"text": "Does the platform\\\'s feature set meet your needs?",'
        ' "answer_type": "yes_no"}]'
    )

    first = await GenerationService(
        session, llm=FakeLLM({"title": "A", "questions": with_newline})
    ).generate_draft("a", author)
    assert first.questions[0].text == "How often do you\nreview dashboards?"

    second = await GenerationService(
        session, llm=FakeLLM({"title": "B", "questions": escaped_quote})
    ).generate_draft("b", author)
    assert second.questions[0].text == "Does the platform's feature set meet your needs?"


async def test_a_string_that_is_not_json_still_fails_loudly(session, author):
    """The repair only undoes a clean JSON encoding; real junk keeps failing."""
    junk = {"title": "X", "questions": "just some prose, not a list"}
    fake = FakeLLM(junk, junk)
    with pytest.raises(LLMError):
        await GenerationService(session, llm=fake).generate_draft("x", author)
    assert fake.calls == 2  # one retry, then loud failure


async def test_options_on_non_select_questions_are_dropped_not_fatal(session, author):
    """A live run failed 16 validations because the model decorated rating questions
    with options [1, 2, 3, 4, 5]. Options mean nothing off the select types, so they
    are dropped instead of burning the retry."""
    decorated = {
        "title": "Engagement",
        "questions": [
            {"text": "How satisfied are you?", "answer_type": "rating", "options": [1, 2, 3, 4, 5]},
            {"text": "Which team?", "answer_type": "single_select", "options": ["A", "B"]},
        ],
    }
    fake = FakeLLM(decorated)
    template = await GenerationService(session, llm=fake).generate_draft("engagement", author)

    assert fake.calls == 1  # repaired, not retried
    assert template.questions[0].options == []
    assert template.questions[1].options == ["A", "B"]  # select options untouched
