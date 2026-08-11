"""The published snapshot is validated once, so no reader has to guess.

The bug these guard: with no ``required`` key, ``engine._briefing`` told the model the
question was required while ``router._to_read`` told the browser it was optional — the
same question, at the same moment, mandatory to the interviewer and skippable to the
respondent. Nothing failed; the two halves simply disagreed, quietly.
"""

import uuid

import pytest

from app.conduct import engine
from app.conduct.engine import _briefing
from app.errors import ValidationError
from app.templates.snapshot import questions_of


def _snap(**kw: object) -> dict[str, object]:
    return {
        "id": str(uuid.uuid4()),
        "position": 0,
        "text": "What is your role?",
        "answer_type": "short_text",
        "options": [],
        "allow_other": False,
        "required": True,
        "follow_up_policy": "never",
        **kw,
    }


def test_a_question_missing_required_is_refused_not_guessed() -> None:
    """The exact shape that made the two readers disagree."""
    broken = _snap()
    del broken["required"]
    with pytest.raises(ValidationError) as exc:
        questions_of({"questions": [broken]})
    assert "required" in str(exc.value)


@pytest.mark.parametrize(
    "field", ["id", "text", "answer_type", "options", "allow_other", "follow_up_policy"]
)
def test_every_other_missing_field_is_refused_too(field: str) -> None:
    """Not a special case for one key — the whole shape is the contract."""
    broken = _snap()
    del broken[field]
    with pytest.raises(ValidationError) as exc:
        questions_of({"questions": [broken]})
    assert field in str(exc.value)


def test_the_error_names_the_field_and_the_question() -> None:
    """A malformed version is a fault to diagnose, so the message must locate it."""
    with pytest.raises(ValidationError) as exc:
        questions_of({"questions": [_snap(), _snap(position=1, answer_type="hologram")]})
    assert "1.answer_type" in str(exc.value)


def test_show_when_is_optional_because_older_versions_predate_it() -> None:
    """The one real default: absence means 'always shown', not a missing value."""
    without = _snap()
    assert "show_when" not in without
    assert questions_of({"questions": [without]})[0]["show_when"] is None


def test_a_version_published_under_the_old_boolean_still_reads() -> None:
    """`follow_up_policy` replaced `allow_follow_ups`, and a published version is
    immutable, so both shapes exist in the table forever. The boolean bought exactly what
    `when_unclear` buys, so that is what it resolves to: reading it as `always_once` would
    change how a survey already in flight is conducted, which publishing is meant to make
    impossible."""
    old = _snap()
    del old["follow_up_policy"]

    permitted = questions_of({"questions": [{**old, "allow_follow_ups": True}]})[0]
    refused = questions_of({"questions": [{**old, "allow_follow_ups": False}]})[0]

    assert permitted["follow_up_policy"] == "when_unclear"
    assert refused["follow_up_policy"] == "never"


def test_a_new_version_is_read_as_written_not_derived() -> None:
    """The policy wins where both are present, and `always_once` survives the round trip
    it exists for."""
    assert (
        questions_of({"questions": [_snap(follow_up_policy="always_once")]})[0]["follow_up_policy"]
        == "always_once"
    )
    both = _snap(follow_up_policy="always_once", allow_follow_ups=False)
    assert questions_of({"questions": [both]})[0]["follow_up_policy"] == "always_once"


def test_a_definition_carrying_neither_is_refused() -> None:
    """Not a default. Every version ever published carries one of the two, so a document
    with neither was written by code that never existed, and guessing on its behalf is
    what this whole module exists to stop."""
    neither = _snap()
    del neither["follow_up_policy"]
    with pytest.raises(ValidationError) as exc:
        questions_of({"questions": [neither]})
    assert "follow_up_policy" in str(exc.value)


def test_a_definition_with_no_questions_key_fails_loudly() -> None:
    with pytest.raises(ValidationError):
        questions_of({})


def test_a_questions_value_that_is_not_a_list_fails_loudly() -> None:
    with pytest.raises(ValidationError) as exc:
        questions_of({"questions": {"0": _snap()}})
    assert "dict" in str(exc.value)


def test_questions_come_back_in_position_order() -> None:
    """Callers index by position; the stored order is not guaranteed to match."""
    out = questions_of({"questions": [_snap(position=2), _snap(position=0), _snap(position=1)]})
    assert [q["position"] for q in out] == [0, 1, 2]


def test_the_engine_loads_through_the_same_gate() -> None:
    """The validating loader is the conduct engine's only door to a snapshot.

    Asserted by identity rather than by calling it: the engine used to wrap this in a
    private passthrough, and a wrapper is exactly where a future edit could start
    reading a definition around the gate instead of through it.
    """
    assert engine.questions_of is questions_of


def test_a_validated_question_briefs_as_required() -> None:
    """The reader that used to default to True now reads a guaranteed key."""
    questions = questions_of({"questions": [_snap(required=True)]})
    state = {"scripted_recorded": False, "follow_ups_used": 0}
    assert "- This question is required" in _briefing(questions, 0, questions[0], state, None, None)


def test_a_validated_optional_question_briefs_as_optional() -> None:
    questions = questions_of({"questions": [_snap(required=False)]})
    state = {"scripted_recorded": False, "follow_ups_used": 0}
    assert "OPTIONAL" in _briefing(questions, 0, questions[0], state, None, None)
