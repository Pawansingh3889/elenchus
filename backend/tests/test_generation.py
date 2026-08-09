"""Generation tests with the LLM mocked at the client boundary (no API key needed)."""

from typing import Any

import pytest

from app.errors import NotFoundError
from app.llm.client import LLMError, ToolTurn
from app.templates.enums import AnswerType, TemplateStatus
from app.templates.generation import GenerationService
from app.templates.schemas import QuestionInput
from app.templates.service import TemplateService
from tests.builders import update_of


class FakeLLM:
    """Returns canned tool payloads in order (repeating the last), each wrapped in a
    ToolTurn with the given note — mirroring the real ``tool_turn`` the service now uses."""

    def __init__(self, *payloads: dict[str, Any], note: str = "Drafted it.") -> None:
        self._payloads = list(payloads)
        self._note = note
        self.calls = 0
        # What the model was actually told. A refine returns the whole survey, so
        # anything missing from the brief is deleted rather than left alone.
        self.messages_seen: list[list[dict[str, str]]] = []

    async def tool_turn(self, *, messages: list[dict[str, str]], **_: Any) -> ToolTurn:
        self.messages_seen.append(messages)
        payload = self._payloads[min(self.calls, len(self._payloads) - 1)]
        self.calls += 1
        return ToolTurn(text=self._note, tool_name="draft_survey_template", tool_input=payload)


_VALID: dict[str, Any] = {
    "title": "Onboarding",
    "description": "New starter survey",
    "questions": [
        {"text": "Your role?", "answer_type": "single_select", "options": ["Lead", "Operator"]},
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
    template, _ = await GenerationService(session, llm=fake).generate_draft("onboarding", author)
    assert fake.calls == 1
    assert template.title == "Onboarding"
    assert template.status is TemplateStatus.draft
    assert [q.text for q in template.questions] == ["Your role?", "Systems used?"]


async def test_generate_returns_the_models_note(session, author):
    fake = FakeLLM(_VALID, note="Added a systems question to see what staff actually use.")
    _, note = await GenerationService(session, llm=fake).generate_draft("onboarding", author)
    assert note == "Added a systems question to see what staff actually use."


async def test_note_from_the_tool_field_is_preferred_over_spoken_text(session, author):
    """A forced tool call suppresses prose, so the note rides in the schema's note field;
    it's read from there (and ignored by template validation)."""
    payload = {**_VALID, "note": "Kept it to two quick questions."}
    _, note = await GenerationService(session, llm=FakeLLM(payload, note="")).generate_draft(
        "x", author
    )
    assert note == "Kept it to two quick questions."


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
    template, _ = await GenerationService(session, llm=fake).generate_draft("teams", author)

    team, tools, site = template.questions
    assert (team.options, team.allow_other) == (["Sales", "Engineering"], True)
    assert (tools.options, tools.allow_other) == (["ERP", "BI"], True)
    # Untouched: nothing to strip, so no write-in is silently opened up.
    assert (site.options, site.allow_other) == (["Hull", "Leeds"], False)


async def test_a_select_of_only_catch_alls_keeps_them_rather_than_emptying(session, author):
    """Stripping every option would leave a select with none — which the schema refuses on
    the way in, but the strip runs after validation and is never re-checked. The engine
    would then offer the question with no enum, quietly turning it into free text."""
    fake = FakeLLM(
        {
            "title": "Onboarding",
            "questions": [
                {
                    "text": "Which team?",
                    "answer_type": "single_select",
                    "options": ["Other", "N/A", "Prefer not to say"],
                },
                {
                    "text": "Which tools?",
                    "answer_type": "multi_select",
                    "options": ["None of the above", "Not applicable"],
                },
            ],
        }
    )
    template, _ = await GenerationService(session, llm=fake).generate_draft("teams", author)

    team, tools = template.questions
    assert team.options == ["Other", "N/A", "Prefer not to say"]
    assert tools.options == ["None of the above", "Not applicable"]
    assert [q.allow_other for q in (team, tools)] == [False, False]


async def test_generate_retries_once_then_succeeds(session, author):
    fake = FakeLLM(_INVALID, _VALID)
    template, _ = await GenerationService(session, llm=fake).generate_draft("x", author)
    assert fake.calls == 2
    assert template.title == "Onboarding"


async def test_generate_fails_loudly_after_retry(session, author):
    fake = FakeLLM(_INVALID, _INVALID)
    with pytest.raises(LLMError):
        await GenerationService(session, llm=fake).generate_draft("x", author)
    assert fake.calls == 2


async def test_a_title_with_no_questions_is_rejected_not_persisted(session, author):
    """A weaker model can return a schema-valid but empty tool call: a title, no
    questions. Caught live from a free auto-routed backup model — schema-valid,
    useless, and previously created a survey with nothing to answer."""
    empty = {"title": "Team Retrospective Survey", "questions": []}
    fake = FakeLLM(empty, empty)
    with pytest.raises(LLMError):
        await GenerationService(session, llm=fake).generate_draft("x", author)
    assert fake.calls == 2  # one retry, then loud failure


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
                {"text": "Your role?", "answer_type": "yes_no"},
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
    template, _ = await GenerationService(session, llm=fake).generate_draft("onboarding", author)

    assert fake.calls == 1  # repaired, not retried
    assert [q.text for q in template.questions] == ["Your role?", "Which shift?"]
    assert template.questions[1].options == ["Days", "Nights"]


async def test_almost_json_with_model_corruptions_is_still_decoded(session, author):
    """Two classic small-model corruptions of an otherwise-correct encoding must not
    defeat the repair: a literal newline inside a string value (invalid in strict
    JSON) and the Python-style \\' escape (never valid JSON). A live run failed on a
    stringified list that plain json.loads refused."""
    with_newline = '[{"text": "How often do you\nreview dashboards?", "answer_type": "number"}]'
    escaped_quote = (
        '[{"text": "Does the platform\\\'s feature set meet your needs?",'
        ' "answer_type": "yes_no"}]'
    )

    first, _ = await GenerationService(
        session, llm=FakeLLM({"title": "A", "questions": with_newline})
    ).generate_draft("a", author)
    assert first.questions[0].text == "How often do you\nreview dashboards?"

    second, _ = await GenerationService(
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
    template, _ = await GenerationService(session, llm=fake).generate_draft("engagement", author)

    assert fake.calls == 1  # repaired, not retried
    assert template.questions[0].options == []
    assert template.questions[1].options == ["A", "B"]  # select options untouched


# --- follow-up refinement ------------------------------------------------------


async def test_refine_updates_the_draft_in_place_and_returns_a_note(session, author):
    original, _ = await GenerationService(session, llm=FakeLLM(_VALID)).generate_draft("x", author)

    revised = {
        "title": "Onboarding (short)",
        "questions": [{"text": "Your role?", "answer_type": "yes_no"}],
    }
    fake = FakeLLM(revised, note="Trimmed it to a single question.")
    updated, note = await GenerationService(session, llm=fake).refine_draft(
        original.id, "make it shorter", author
    )

    assert updated.id == original.id  # same draft, revised in place
    assert updated.title == "Onboarding (short)"
    assert [q.text for q in updated.questions] == ["Your role?"]
    assert note == "Trimmed it to a single question."


_WITH_CONDITION: dict[str, Any] = {
    "title": "Onboarding",
    "questions": [
        {"text": "Your role?", "answer_type": "single_select", "options": ["Manager", "Line lead"]},
        {
            "text": "How big is your team?",
            "answer_type": "number",
            "show_when": {"question": 0, "op": "is", "value": "Manager"},
        },
    ],
}


async def test_refine_tells_the_model_which_conditions_it_must_keep(session, author):
    """A refine returns the COMPLETE survey and update_draft replaces every row with it,
    so an attribute the brief omits is deleted, not left alone. show_when was omitted, so
    the first unrelated refine silently dropped every conditional-visibility rule and the
    builder then re-seeded from the response, showing the author "Always"."""
    original, _ = await GenerationService(session, llm=FakeLLM(_WITH_CONDITION)).generate_draft(
        "onboarding", author
    )
    assert original.questions[1].show_when is not None  # the draft really has one

    fake = FakeLLM(_WITH_CONDITION, note="Made it optional.")
    await GenerationService(session, llm=fake).refine_draft(
        original.id, "make question 2 optional", author
    )

    brief = fake.messages_seen[0][0]["content"]
    # Numbered as the brief numbers its questions, from 1, not the stored 0-based index.
    assert 'shown only if Q1 is "Manager"' in brief


async def test_refine_keeps_a_condition_the_model_returns(session, author):
    """The other half: the brief carries the condition out, and the round trip carries
    it back in. Without this the first test could pass while update_draft dropped it."""
    original, _ = await GenerationService(session, llm=FakeLLM(_WITH_CONDITION)).generate_draft(
        "onboarding", author
    )

    fake = FakeLLM(_WITH_CONDITION, note="Unchanged.")
    updated, _ = await GenerationService(session, llm=fake).refine_draft(
        original.id, "no change", author
    )

    kept = sorted(updated.questions, key=lambda q: q.position)[1].show_when
    assert kept == {"question": 0, "op": "is", "value": "Manager"}


async def test_refine_re_validates_so_a_bad_change_fails_loudly(session, author):
    original, _ = await GenerationService(session, llm=FakeLLM(_VALID)).generate_draft("x", author)

    fake = FakeLLM(_INVALID, _INVALID)  # every attempt invalid
    with pytest.raises(LLMError):
        await GenerationService(session, llm=fake).refine_draft(original.id, "break it", author)


async def test_refine_refuses_another_authors_template(session, author, other_author):
    original, _ = await GenerationService(session, llm=FakeLLM(_VALID)).generate_draft("x", author)

    with pytest.raises(NotFoundError):
        await GenerationService(session, llm=FakeLLM(_VALID)).refine_draft(
            original.id, "change it", other_author
        )


_FREE_TEXT_DRAFT: dict[str, Any] = {
    "title": "Compliance check",
    "questions": [
        {"text": "How familiar are you with the standards?", "answer_type": "rating"},
        {"text": "What challenges do you face?", "answer_type": "short_text"},
    ],
}
_CLOSED_DRAFT: dict[str, Any] = {
    "title": "Compliance check",
    "questions": [
        {"text": "How familiar are you with the standards?", "answer_type": "rating"},
        {
            "text": "What challenges do you face?",
            "answer_type": "multi_select",
            "options": ["Time", "Training", "Equipment"],
            "allow_other": True,
        },
    ],
}


async def test_a_generated_survey_has_no_free_text(session, author):
    """The rule, on the path an author actually uses. Nobody sets this per survey: a
    drafted survey is conducted by an interviewer that has to judge whether a reply
    answered the question, and an open box is where that judgement is hardest."""
    fake = FakeLLM(_FREE_TEXT_DRAFT, _CLOSED_DRAFT)
    template, _ = await GenerationService(session, llm=fake).generate_draft("compliance", author)

    assert fake.calls == 2  # rejected, then retried with the reason
    assert AnswerType.short_text not in {q.answer_type for q in template.questions}
    assert AnswerType.long_text not in {q.answer_type for q in template.questions}


async def test_a_model_that_insists_on_free_text_fails_loudly(session, author):
    """No silent repair. A survey quietly stripped of the question the author asked for
    is worse than an error, because nobody would know to look for it."""
    fake = FakeLLM(_FREE_TEXT_DRAFT, _FREE_TEXT_DRAFT)
    with pytest.raises(LLMError, match="short_text"):
        await GenerationService(session, llm=fake).generate_draft("compliance", author)


async def test_the_rule_is_stated_before_the_model_answers(session, author):
    """The check holds the line; saying it up front spends the retry on real mistakes."""
    fake = FakeLLM(_CLOSED_DRAFT)
    await GenerationService(session, llm=fake).generate_draft("compliance", author)

    brief = fake.messages_seen[0][0]["content"]
    assert "Free text is not available" in brief
    assert "short_text" not in brief.split("ONLY")[1].split(".")[0]


async def test_a_refine_may_not_introduce_free_text(session, author):
    """The half that kept coming undone. A refine carries one instruction and no memory
    of the last, so the rule cannot live in what the author said earlier."""
    original, _ = await GenerationService(session, llm=FakeLLM(_CLOSED_DRAFT)).generate_draft(
        "compliance", author
    )

    added_text = {
        "title": "Compliance check",
        "questions": [
            *_CLOSED_DRAFT["questions"],
            {"text": "What training would help?", "answer_type": "short_text"},
        ],
    }
    complied = {
        "title": "Compliance check",
        "questions": [
            *_CLOSED_DRAFT["questions"],
            {
                "text": "What training would help?",
                "answer_type": "multi_select",
                "options": ["Induction", "Refreshers"],
                "allow_other": True,
            },
        ],
    }
    fake = FakeLLM(added_text, complied)
    updated, _ = await GenerationService(session, llm=fake).refine_draft(
        original.id, "add a question about training", author
    )

    assert fake.calls == 2
    assert AnswerType.short_text not in {q.answer_type for q in updated.questions}


async def test_a_text_question_the_author_added_survives_a_refine(session, author):
    """The rule constrains what the model writes on the author's behalf, not what the
    author may ask for. A blanket check would reject the survey for carrying the author's
    own question back, and they would find it deleted or every refine failing."""
    original, _ = await GenerationService(session, llm=FakeLLM(_CLOSED_DRAFT)).generate_draft(
        "compliance", author
    )
    mine = "Anything else we should know?"
    with_text = await TemplateService(session).update_draft(
        original.id,
        update_of(
            original,
            questions=[
                *[
                    QuestionInput(
                        text=q.text,
                        answer_type=q.answer_type,
                        options=q.options,
                        allow_other=q.allow_other,
                    )
                    for q in sorted(original.questions, key=lambda q: q.position)
                ],
                QuestionInput(text=mine, answer_type=AnswerType.long_text),
            ],
        ),
        author,
    )
    assert AnswerType.long_text in {q.answer_type for q in with_text.questions}

    returned = {
        "title": "Compliance check",
        "questions": [
            *_CLOSED_DRAFT["questions"],
            {"text": mine, "answer_type": "long_text"},
        ],
    }
    fake = FakeLLM(returned)
    updated, _ = await GenerationService(session, llm=fake).refine_draft(
        original.id, "tidy the wording", author
    )

    assert fake.calls == 1  # accepted first time: nothing new was introduced
    assert mine in {q.text for q in updated.questions}
