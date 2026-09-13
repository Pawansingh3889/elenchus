"""Similarity, projection and grouping over embedding vectors, in plain Python and seeded.

Sized for this service: a survey's answers are tens to hundreds of short texts, where a
dense matrix in Python is milliseconds and a numerical library would be a dependency with
nothing to do. Every random choice is seeded, so the same answers always draw the same map
and the same themes.
"""

import math
import random
from collections.abc import Sequence

SEED = 13


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity. A zero vector has no direction, which is a malformed input."""
    if len(a) != len(b):
        raise ValueError(f"vectors differ in length: {len(a)} and {len(b)}")
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        raise ValueError("a zero vector has no direction to compare")
    return sum(x * y for x, y in zip(a, b, strict=True)) / (na * nb)


def _unit(v: Sequence[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v))
    if n == 0:
        raise ValueError("a zero vector has no direction to compare")
    return [x / n for x in v]


def project_2d(vectors: Sequence[Sequence[float]], rounds: int = 200) -> list[tuple[float, float]]:
    """The first two principal components of the vectors, one point each.

    Through the n-by-n Gram matrix of the centred vectors rather than the covariance, since
    here there are far fewer texts than dimensions. Power iteration with deflation finds
    the top two eigenvectors; a point's coordinates are those eigenvectors scaled by the
    square roots of their eigenvalues. Axes carry no units: only distances mean anything.
    """
    n = len(vectors)
    if n == 0:
        return []
    if n == 1:
        return [(0.0, 0.0)]
    dims = len(vectors[0])
    mean = [sum(v[d] for v in vectors) / n for d in range(dims)]
    centred = [[v[d] - mean[d] for d in range(dims)] for v in vectors]
    gram = [[sum(x * y for x, y in zip(a, b, strict=True)) for b in centred] for a in centred]
    rng = random.Random(SEED)
    components: list[tuple[float, list[float]]] = []
    for _ in range(2):
        vec = [rng.uniform(-1, 1) for _ in range(n)]
        value = 0.0
        for _ in range(rounds):
            nxt = [sum(gram[i][j] * vec[j] for j in range(n)) for i in range(n)]
            for _value, other in components:
                dot = sum(a * b for a, b in zip(nxt, other, strict=True))
                nxt = [a - dot * b for a, b in zip(nxt, other, strict=True)]
            size = math.sqrt(sum(x * x for x in nxt))
            if size == 0:
                break
            value = size
            vec = [x / size for x in nxt]
        # Deflate the Gram matrix's own copy of this component out of later iterations.
        components.append((value, vec))
        gram = [[gram[i][j] - value * vec[i] * vec[j] for j in range(n)] for i in range(n)]
    (v1, e1), (v2, e2) = components
    s1, s2 = math.sqrt(max(v1, 0.0)), math.sqrt(max(v2, 0.0))
    return [(e1[i] * s1, e2[i] * s2) for i in range(n)]


def kmeans(vectors: Sequence[Sequence[float]], k: int, rounds: int = 50) -> list[int]:
    """Spherical k-means: groups by direction, which is what similarity of meaning is.

    Seeded k-means++ initialisation, so a small change to the answers does not reshuffle
    every theme. Returns a group index per vector, numbered by first appearance.
    """
    n = len(vectors)
    if n == 0:
        return []
    k = max(1, min(k, n))
    units = [_unit(v) for v in vectors]
    rng = random.Random(SEED)
    centres = [units[rng.randrange(n)]]
    while len(centres) < k:
        distance = [
            1 - max(sum(a * b for a, b in zip(u, c, strict=True)) for c in centres) for u in units
        ]
        total = sum(distance)
        if total <= 0:
            break
        pick, running = rng.uniform(0, total), 0.0
        for index, d in enumerate(distance):
            running += d
            if running >= pick:
                centres.append(units[index])
                break
    assignment = [0] * n
    for _ in range(rounds):
        changed = False
        for i, u in enumerate(units):
            best = max(
                range(len(centres)),
                key=lambda c: sum(a * b for a, b in zip(u, centres[c], strict=True)),
            )
            if best != assignment[i]:
                assignment[i], changed = best, True
        for c in range(len(centres)):
            members = [units[i] for i in range(n) if assignment[i] == c]
            if members:
                centres[c] = _unit([sum(m[d] for m in members) for d in range(len(members[0]))])
        if not changed:
            break
    renumber: dict[int, int] = {}
    return [renumber.setdefault(group, len(renumber)) for group in assignment]


def near_duplicates(
    vectors: Sequence[Sequence[float]], threshold: float
) -> list[tuple[int, int, float]]:
    """Every pair at or above the threshold, most similar first."""
    units = [_unit(v) for v in vectors]
    pairs = [
        (i, j, sum(a * b for a, b in zip(units[i], units[j], strict=True)))
        for i in range(len(units))
        for j in range(i + 1, len(units))
    ]
    return sorted((p for p in pairs if p[2] >= threshold), key=lambda p: -p[2])
