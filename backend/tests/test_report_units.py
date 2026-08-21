"""The results page reports a number question's stats in its display unit.

Temperature is affine, so each answer must be converted before averaging: averaging the
Celsius values and then converting would put a freezer at the wrong Fahrenheit. The test
pins the correct order by checking 0 C and 20 C average to 50 F, not the (wrong) 10 C.
"""

import pytest

from app.runs.schemas import QuestionReport
from app.runs.service import _report_question


def _number_question(unit: str | None, display_unit: str | None) -> dict:
    return {
        "id": "00000000-0000-0000-0000-000000000001",
        "position": 0,
        "text": "Core temp?",
        "answer_type": "number",
        "options": [],
        "unit": unit,
        "display_unit": display_unit,
    }


def test_number_stats_stay_in_primary_unit_without_display() -> None:
    report: QuestionReport = _report_question(
        _number_question("C", None),
        [{"number": 0}, {"number": 20}],
        [],
        0,
    )
    assert report.unit == "C"
    assert report.average == 10.0
    assert report.low == 0.0 and report.high == 20.0


def test_number_stats_converted_per_value_into_display_unit() -> None:
    # 0 C = 32 F, 20 C = 68 F -> average 50 F. Converting the average (10 C) would give
    # 50 F by coincidence here, but the extremes prove per-value: low 32 F, high 68 F.
    report: QuestionReport = _report_question(
        _number_question("C", "F"),
        [{"number": 0}, {"number": 20}],
        [],
        0,
    )
    assert report.display_unit == "F"
    # Floating-point dust: 0 C is 32 F to within rounding.
    assert report.low == pytest.approx(32.0)
    assert report.high == pytest.approx(68.0)
    assert report.average == pytest.approx(50.0)


def test_rating_stats_are_never_converted() -> None:
    question = _number_question("C", "F")
    question["answer_type"] = "rating"
    report: QuestionReport = _report_question(
        question,
        [{"rating": 2}, {"rating": 4}],
        [],
        0,
    )
    # A rating is a 1-5 scale, not a measured quantity: 2 and 4 average to 3, not 3 F.
    # The unit fields are still carried through, but the numbers are never converted.
    assert report.average == 3.0
    assert report.low == 2.0 and report.high == 4.0
    assert report.unit == "C" and report.display_unit == "F"
