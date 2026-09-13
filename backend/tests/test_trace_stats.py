"""Rank correlation and its interval, against answers worked out by hand."""

import pytest

from app.trace.stats import MIN_SAMPLES, bootstrap_interval, ranks, spearman


def test_ties_share_the_average_of_their_ranks():
    assert ranks([10, 20, 20, 30]) == [1.0, 2.5, 2.5, 4.0]


def test_a_perfectly_monotonic_relationship_is_one_whatever_its_shape():
    xs = [1, 2, 3, 4, 5, 6]
    assert spearman(xs, [x**3 for x in xs]) == pytest.approx(1.0)
    assert spearman(xs, [-x for x in xs]) == pytest.approx(-1.0)


def test_a_known_value_with_ties():
    # Worked by hand: ranks x = [1, 2.5, 2.5, 4], y = [1, 3, 2, 4]; Pearson on ranks = 0.9487.
    assert spearman([1, 2, 2, 3], [10, 30, 20, 40]) == pytest.approx(0.948683, abs=1e-6)


def test_no_variation_has_no_coefficient_rather_than_zero():
    assert spearman([3, 3, 3, 3], [1, 2, 3, 4]) is None
    assert spearman([1], [1]) is None


def test_the_interval_brackets_a_strong_relationship_and_is_repeatable():
    xs = list(range(MIN_SAMPLES + 10))
    ys = [x + (7 if x % 5 == 0 else 0) for x in xs]
    rho = spearman(xs, ys)
    first = bootstrap_interval(xs, ys)
    assert rho is not None and first is not None
    low, high = first
    assert low <= rho <= high
    assert low > 0.8
    assert bootstrap_interval(xs, ys) == first  # seeded: the same slice, the same numbers
