"""Measuring semantic grounding against labelled pairs, before it is allowed near a respondent.

A first measurement on 13 Sep 2026 tried one absolute similarity threshold between what
was said and the chosen option, and it was too fragile to use: short sentences and short
option labels sit in a narrow band of similarity, and the best threshold cleared the nearest
wrong answer by 0.009. So the question asked is relative instead, and it is the question
the gate actually has: of the options this question offered, is the chosen one the closest
to what was said, and by how much over the runner-up?

A margin is only recommended if it accepts none of the labelled negatives the word check
refused, and the lowest such margin is the one recommended, because every step above it
refuses more real answers for no measured gain. It is a measurement of this set with this
model; a different model needs measuring again.
"""

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LabelledPair:
    said: str
    option: str
    options: tuple[str, ...]
    supported: bool
    language: str
    source: str


@dataclass(frozen=True)
class Judged:
    pair: LabelledPair
    # What the existing word check concluded, before any similarity is consulted.
    word_supported: bool
    similarity: float
    # The chosen option's similarity less the best other option's: positive only when the
    # chosen option is the closest of the question's options to what was said.
    margin: float


@dataclass(frozen=True)
class SweepRow:
    margin: float
    # Negatives the gate would accept: answers nobody gave.
    false_accepts: int
    # Positives the gate would still refuse: real answers lost.
    false_refusals: int


def load_pairs(path: Path) -> list[LabelledPair]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    pairs = []
    for item in raw["pairs"]:
        pair = LabelledPair(**{**item, "options": tuple(item["options"])})
        if pair.option not in pair.options:
            raise ValueError(f"labelled option {pair.option!r} is not among its options")
        if len(pair.options) < 2:
            raise ValueError(f"a margin needs two options or more: {pair.said!r}")
        pairs.append(pair)
    return pairs


def margin_over_rest(option: str, similarity: Mapping[str, float]) -> float:
    """How far the option's similarity is above the best of the other options'."""
    others = [score for name, score in similarity.items() if name != option]
    if not others:
        raise ValueError("a margin needs at least one other option to beat")
    return similarity[option] - max(others)


def judge(
    pairs: Sequence[LabelledPair],
    word_supported: Callable[[LabelledPair], bool],
    similarities: Sequence[Mapping[str, float]],
) -> list[Judged]:
    """Pair each label with the word check's verdict and its option similarities."""
    if len(similarities) != len(pairs):
        raise ValueError(f"{len(similarities)} similarity sets for {len(pairs)} pairs")
    return [
        Judged(
            pair=p,
            word_supported=word_supported(p),
            similarity=s[p.option],
            margin=margin_over_rest(p.option, s),
        )
        for p, s in zip(pairs, similarities, strict=True)
    ]


def accepted(item: Judged, margin: float | None) -> bool:
    """The gate's decision: the word check, then the margin only where words failed."""
    if item.word_supported:
        return True
    return margin is not None and item.margin >= margin


def sweep(judged: Sequence[Judged], margins: Sequence[float]) -> list[SweepRow]:
    return [
        SweepRow(
            margin=m,
            false_accepts=sum(1 for j in judged if not j.pair.supported and accepted(j, m)),
            false_refusals=sum(1 for j in judged if j.pair.supported and not accepted(j, m)),
        )
        for m in margins
    ]


@dataclass(frozen=True)
class Recommendation:
    margin: float
    # The closest a wrong answer the word check refused came: the margin must stay above it.
    highest_negative: float
    # The lowest margin among the real answers the recommendation still accepts.
    lowest_positive: float


def recommend(judged: Sequence[Judged]) -> Recommendation | None:
    """The midpoint of the gap between the wrong answers and the real ones.

    A margin must sit above every labelled negative the word check refused, or it records
    an answer nobody gave. Any margin up to the lowest real answer above that line refuses
    the same real answers, so the midpoint is chosen rather than the lowest: the first
    measurement picked the lowest and cleared the nearest wrong answer by 0.009, which is
    a gate that holds only on the day it was measured. Both edges are returned so the
    headroom is visible wherever the number is.

    Negatives the word check already accepts (O13, O14) are out of any margin's reach and
    are left to the word check. None when the set has no negative to stay above, when no
    real answer clears the highest one, or when the gap is too narrow to put a margin in.
    """
    negatives = [j.margin for j in judged if not j.pair.supported and not j.word_supported]
    if not negatives:
        return None
    ceiling = max(negatives)
    above = [
        j.margin
        for j in judged
        if j.pair.supported and not j.word_supported and j.margin > max(ceiling, 0.0)
    ]
    if not above:
        return None
    floor = min(above)
    # Never below zero: a negative margin would accept an option that is not the closest.
    margin = round(max((ceiling + floor) / 2, 0.0), 3)
    if not ceiling < margin <= floor:
        return None
    return Recommendation(margin=margin, highest_negative=ceiling, lowest_positive=floor)
