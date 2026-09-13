"""Rank correlation with an honest interval, in plain Python.

Spearman rather than Pearson because the factors here are skewed counts and the outcomes
are latencies with long tails: ranks are robust to both, and to a relationship that is
monotonic without being straight. The interval is a percentile bootstrap, seeded so the
same slice always shows the same numbers.

A coefficient from few samples is mostly noise, so below ``MIN_SAMPLES`` it is still
computed, for anyone who opens the table, but flagged and given no interval. A side with no
variation has no rank order at all, and its coefficient is None rather than zero.
"""

import math
import random
from collections.abc import Sequence

MIN_SAMPLES = 20
BOOTSTRAP_ROUNDS = 1000
SEED = 13


def ranks(values: Sequence[float]) -> list[float]:
    """1-based ranks, ties sharing the average of the ranks they span."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    result = [0.0] * len(values)
    start = 0
    while start < len(order):
        end = start
        while end + 1 < len(order) and values[order[end + 1]] == values[order[start]]:
            end += 1
        shared = (start + end) / 2 + 1
        for position in range(start, end + 1):
            result[order[position]] = shared
        start = end + 1
    return result


def pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    n = len(xs)
    if n < 2:
        return None
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    dx = [x - mean_x for x in xs]
    dy = [y - mean_y for y in ys]
    spread = math.sqrt(sum(d * d for d in dx) * sum(d * d for d in dy))
    if spread == 0:
        return None
    return sum(a * b for a, b in zip(dx, dy, strict=True)) / spread


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    return pearson(ranks(xs), ranks(ys))


def bootstrap_interval(
    xs: Sequence[float], ys: Sequence[float], rounds: int = BOOTSTRAP_ROUNDS, seed: int = SEED
) -> tuple[float, float] | None:
    """The 2.5th and 97.5th percentiles of Spearman over resampled pairs.

    Resamples with no variation on one side have no coefficient and are skipped; if most
    are skipped the interval says nothing and None is returned.
    """
    rng = random.Random(seed)
    n = len(xs)
    draws: list[float] = []
    for _ in range(rounds):
        picks = [rng.randrange(n) for _ in range(n)]
        rho = spearman([xs[i] for i in picks], [ys[i] for i in picks])
        if rho is not None:
            draws.append(rho)
    if len(draws) < rounds // 2:
        return None
    draws.sort()
    low = draws[int(0.025 * (len(draws) - 1))]
    high = draws[int(math.ceil(0.975 * (len(draws) - 1)))]
    return low, high
