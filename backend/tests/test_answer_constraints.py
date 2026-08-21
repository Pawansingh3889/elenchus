"""The conversational route must not let a structured question be answered with the
wrong shape. A numeric question answered "hot" is not a number, and the engine's own
record-time gate (`_unrecordable`, shared by the model's record_answer tool) must reject
it before any value is stored. These pin that contract so a future change cannot quietly
let free text into a structured cell.
"""

import pytest

from app.conduct.engine import _unrecordable
from app.conduct.validation import AnswerValidationError, validate_answer


def _question(answer_type: str, **over: object) -> dict:
    q: dict = {
        "id": "q1",
        "text": "T",
        "answer_type": answer_type,
        "options": [],
        "allow_other": False,
        "required": True,
    }
    q.update(over)
    return q


def test_number_rejects_text() -> None:
    with pytest.raises(AnswerValidationError):
        validate_answer(_question("number"), "hot")


def test_rating_rejects_text() -> None:
    with pytest.raises(AnswerValidationError):
        validate_answer(_question("rating"), "three")


def test_number_accepts_number() -> None:
    assert validate_answer(_question("number"), 6) == {"number": 6}


def test_unrecordable_flags_wrong_shaped_scripted_answer() -> None:
    # A "number" question given the word "boiling" must be refused at record time, the
    # same gate the model's tool call passes through.
    state = {"scripted_recorded": False}
    assert _unrecordable(_question("number"), state, "boiling", []) is not None


def test_unrecordable_allows_well_shaped_scripted_answer() -> None:
    state = {"scripted_recorded": False}
    assert _unrecordable(_question("number"), state, 6, []) is None


def test_unrecordable_flags_wrong_shaped_rating() -> None:
    state = {"scripted_recorded": False}
    assert _unrecordable(_question("rating"), state, "four", []) is not None
