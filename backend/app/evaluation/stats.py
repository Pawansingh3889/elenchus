"""Rates with honest intervals, in plain Python.

Wilson's score interval rather than the normal approximation, because the rates here sit
near 0 and 1 on small counts, which is exactly where the normal interval reports bounds
below zero or above one. Below ``MIN_LABELLED`` a rate is still computed, for anyone who
opens the table, and flagged as too few to read anything from.
"""

import math

MIN_LABELLED = 20
Z_95 = 1.959964


def wilson(successes: int, trials: int, z: float = Z_95) -> tuple[float, float] | None:
    """The 95% Wilson score interval for successes out of trials, or None with no trials."""
    if trials < 0 or not 0 <= successes <= trials:
        raise ValueError(f"cannot take {successes} successes out of {trials} trials")
    if trials == 0:
        return None
    p = successes / trials
    z2 = z * z
    denominator = 1 + z2 / trials
    centre = (p + z2 / (2 * trials)) / denominator
    margin = z * math.sqrt(p * (1 - p) / trials + z2 / (4 * trials * trials)) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def median(values: list[float]) -> float | None:
    """The middle of what was measured, or None when nothing was."""
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2
