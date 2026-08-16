"""One shape for a survey's questions, so no reader has to guess.

Replaces test_snapshot_contract.py. That file guarded a frozen JSONB definition against
missing keys, and the definition is gone with versions. The bug it existed for is not:
with no ``required`` key, ``engine._briefing`` told the model a question was required
while ``router._to_read`` told the browser it was optional. The same question, at the
same moment, mandatory to the interviewer and skippable to the respondent, with nothing
failing.

What changed is where the guarantee comes from. It used to be validation of a document
that could be malformed; it is now construction from typed columns, so the tests below
assert that `questions_of` emits every key its readers subscript and that the engine
still agrees with the shape. A key silently dropped from `_question_to_dict` is the
modern form of the old bug, and it fails here.
"""

import uuid

import pytest

from app.conduct.engine import _briefing
from app.templates.enums import AnswerType, FollowUpPolicy
from app.templates.models import SurveyQuestion, SurveyTemplate
from app.templates.reading import questions_of, setting_of

# Every key a reader subscripts. Listed rather than derived from the function under test,
# because a list derived from the code cannot notice the code dropping one.
CONTRACT = {
    "id",
    "position",
    "text",
    "answer_type",
    "options",
    "allow_other",
    "required",
    "follow_up_policy",
    "show_when",
}


def _question(**kw: object) -> SurveyQuestion:
    fields: dict[str, object] = {
        "id": uuid.uuid4(),
        "position": 0,
        "text": "How hot does it get?",
        "answer_type": AnswerType.rating,
        "options": [],
        "allow_other": False,
        "required": True,
        "follow_up_policy": FollowUpPolicy.never,
        "show_when": None,
    }
    return SurveyQuestion(**(fields | kw))


def _template(*questions: SurveyQuestion, setting: str | None = None) -> SurveyTemplate:
    template = SurveyTemplate(id=uuid.uuid4(), title="T", setting=setting)
    template.questions.extend(questions)
    return template


def test_every_contract_key_is_present() -> None:
    (question,) = questions_of(_template(_question()))
    assert set(question) == CONTRACT


def test_values_are_json_shapes_not_orm_objects() -> None:
    """The engine and the report treat these as plain data and hand parts of them to a
    model. An enum member reaching a prompt renders as `AnswerType.rating`."""
    (question,) = questions_of(_template(_question()))
    assert question["answer_type"] == "rating"
    assert question["follow_up_policy"] == "never"
    assert isinstance(question["id"], str)


def test_show_when_absent_is_none_rather_than_missing() -> None:
    """Absent means "always shown", and it has to mean that in one place. A missing key
    would leave each reader to decide, which is the bug this file is named for."""
    (question,) = questions_of(_template(_question(show_when=None)))
    assert question["show_when"] is None


def test_questions_come_back_in_position_order() -> None:
    """Position is what the engine walks, and the order of a loaded collection is a
    property of the query rather than of the data."""
    out = questions_of(
        _template(
            _question(position=2, text="third"),
            _question(position=0, text="first"),
            _question(position=1, text="second"),
        )
    )
    assert [q["text"] for q in out] == ["first", "second", "third"]


# What the engine tracks per question while a run is in flight. Spelled out here so the
# briefing calls below read as the engine's own, rather than as a fixture that happens
# to satisfy them.
STATE = {"scripted_recorded": False, "follow_ups_used": 0}


def test_a_required_question_briefs_as_required() -> None:
    """The original disagreement, pinned from the interviewer's side."""
    (question,) = questions_of(_template(_question(required=True)))
    assert "This question is required" in _briefing([question], 0, question, STATE, None, None)


def test_an_optional_question_briefs_as_optional() -> None:
    (question,) = questions_of(_template(_question(required=False)))
    assert "OPTIONAL" in _briefing([question], 0, question, STATE, None, None)


@pytest.mark.parametrize("blank", ["", "   ", "\n"])
def test_a_setting_of_whitespace_reads_as_none(blank: str) -> None:
    """An author who cleared the box has described nothing. Passing "" down would put an
    empty heading in the briefing that announces a setting and then gives none."""
    assert setting_of(_template(setting=blank)) is None


def test_a_described_setting_is_passed_through_trimmed() -> None:
    assert setting_of(_template(setting="  A chilled fish plant.  ")) == "A chilled fish plant."
