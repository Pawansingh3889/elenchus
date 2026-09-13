"""The margin measurement: recommended from the gap, never from a guess."""

import pytest

from app.embeddings.grounding import (
    LabelledPair,
    judge,
    margin_over_rest,
    recommend,
    sweep,
)

OPTIONS = ("Processing", "Dispatch", "Maintenance")


def _pair(option: str, supported: bool) -> LabelledPair:
    return LabelledPair(
        said="s", option=option, options=OPTIONS, supported=supported, language="en", source="t"
    )


def _scored(option_margin: float) -> dict[str, float]:
    """Similarities where Processing leads Dispatch by exactly the given margin."""
    return {"Processing": 0.5, "Dispatch": 0.5 - option_margin, "Maintenance": 0.0}


def test_a_margin_is_the_distance_over_the_best_other_option():
    scores = {"Processing": 0.41, "Dispatch": 0.30, "Maintenance": 0.12}
    assert margin_over_rest("Processing", scores) == pytest.approx(0.11)
    # Not the closest: the margin is negative, whatever the raw similarity.
    assert margin_over_rest("Dispatch", scores) == pytest.approx(-0.11)


def test_the_recommendation_is_the_middle_of_the_gap_and_says_how_wide_it_is():
    pairs = [_pair("Processing", True), _pair("Processing", True), _pair("Processing", False)]
    sims = [_scored(0.20), _scored(0.06), _scored(0.02)]
    judged = judge(pairs, lambda _: False, sims)

    best = recommend(judged)

    assert best is not None
    assert best.margin == pytest.approx(0.04)
    assert best.highest_negative == pytest.approx(0.02)
    assert best.lowest_positive == pytest.approx(0.06)
    (row,) = sweep(judged, [best.margin])
    assert (row.false_accepts, row.false_refusals) == (0, 0)


def test_a_real_answer_below_the_highest_negative_is_given_up_not_chased():
    pairs = [_pair("Processing", True), _pair("Processing", True), _pair("Processing", False)]
    sims = [_scored(0.01), _scored(0.10), _scored(0.04)]
    judged = judge(pairs, lambda _: False, sims)

    best = recommend(judged)

    assert best is not None and best.margin == pytest.approx(0.07)
    (row,) = sweep(judged, [best.margin])
    assert (row.false_accepts, row.false_refusals) == (0, 1)


def test_a_negative_the_word_check_already_accepts_does_not_move_the_gap():
    pairs = [_pair("Processing", True), _pair("Processing", False), _pair("Processing", False)]
    sims = [_scored(0.10), _scored(0.30), _scored(0.02)]
    judged = judge(pairs, lambda p: p is pairs[1], sims)
    best = recommend(judged)
    assert best is not None and best.margin == pytest.approx(0.06)


def test_no_recommendation_without_a_gap_or_without_negatives_to_stay_above():
    positive, negative = _pair("Processing", True), _pair("Processing", False)
    overlapping = judge([positive, negative], lambda _: False, [_scored(0.02), _scored(0.05)])
    assert recommend(overlapping) is None
    no_negatives = judge([positive], lambda _: False, [_scored(0.2)])
    assert recommend(no_negatives) is None
