"""The unit converter and the question schema's unit rules.

Conversion is pure formula, so it is exact and worth pinning: a wrong temperature offset
would make every freezer reading wrong. The schema rules keep ``display_unit`` honest:
known, and the same dimension as ``unit``.
"""

import pytest
from pydantic import ValidationError

from app.templates.schemas import QuestionInput
from app.units import can_convert, conversion_label, convert, is_known_unit


def test_known_units() -> None:
    assert is_known_unit("C") and is_known_unit("F") and is_known_unit("m")
    assert not is_known_unit("banana")


def test_temperature_round_trip() -> None:
    # 0 C is 32 F; back to C is 0 again (within float dust).
    assert abs(convert(convert(0.0, "C", "F"), "F", "C")) < 1e-9
    assert round(convert(100.0, "C", "F"), 6) == 212.0
    assert round(convert(32.0, "F", "C"), 6) == 0.0


def test_length_conversion() -> None:
    assert round(convert(1.0, "km", "m")) == 1000
    assert round(convert(1.0, "mi", "m"), 3) == 1609.344
    assert round(convert(12.0, "in", "cm"), 3) == 30.48


def test_mass_and_volume() -> None:
    assert round(convert(1.0, "t", "kg")) == 1000
    assert round(convert(1.0, "lb", "kg"), 6) == 0.453592
    assert round(convert(1.0, "gal", "l"), 6) == 3.785412


def test_can_convert_same_dimension_only() -> None:
    assert can_convert("C", "F")
    assert can_convert("m", "ft")
    assert not can_convert("C", "m")  # different dimension
    assert not can_convert("m", "m")  # identical is pointless
    assert not can_convert("C", None)


def test_conversion_label() -> None:
    assert conversion_label(32.0, "C", "F") == "32 °C = 89.6 °F"
    assert conversion_label(5.0, "m", "C") is None  # incompatible -> nothing to show


def test_schema_rejects_unknown_unit() -> None:
    with pytest.raises(ValidationError):
        QuestionInput(text="Temp?", answer_type="number", unit="banana")


def test_schema_rejects_mismatched_dimensions() -> None:
    with pytest.raises(ValidationError):
        QuestionInput(text="Temp?", answer_type="number", unit="C", display_unit="m")


def test_schema_accepts_unit_and_display() -> None:
    q = QuestionInput(text="Temp?", answer_type="number", unit="C", display_unit="F")
    assert q.unit == "C" and q.display_unit == "F"


def test_schema_allows_no_unit() -> None:
    q = QuestionInput(text="How many?", answer_type="number")
    assert q.unit is None and q.display_unit is None
