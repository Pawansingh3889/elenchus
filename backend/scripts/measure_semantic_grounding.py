#!/usr/bin/env python3
"""Measure option-relative semantic grounding on the labelled pairs and write the result down.

Live: it embeds every distinct sentence and option once through the real embeddings endpoint
(well under a cent). It uses the LLM_EMBEDDING_* settings if enabled, and otherwise the tier 1
base URL and key with text-embedding-3-small, saying so, because measuring does not need the
deployment to have switched embeddings on.

    cd backend && PYTHONPATH=. uv run python scripts/measure_semantic_grounding.py
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from app.conduct.validation import ungrounded_choice
from app.config import get_settings
from app.embeddings.grounding import judge, load_pairs, recommend, sweep
from app.embeddings.math import cosine
from app.llm.client import EmbedderProtocol
from app.llm.factory import get_embedder
from app.llm.ledger import TierEconomics
from app.llm.openai_compatible import OpenAICompatibleLLMClient

BACKEND = Path(__file__).resolve().parents[1]
PAIRS = BACKEND / "tests" / "fixtures" / "grounding_pairs.json"
# Beside the code that serves it, not under tests/: the lens reads this file.
REPORT = BACKEND / "app" / "embeddings" / "measurements" / "grounding.json"
MARGINS = [round(0.01 * i, 2) for i in range(31)]


def embedder() -> tuple[EmbedderProtocol, str]:
    settings = get_settings()
    if settings.llm_embedding_enabled:
        return get_embedder(), "LLM_EMBEDDING_* settings"
    print("Embeddings are not enabled; measuring through tier 1's endpoint and key instead.")
    economics = TierEconomics(
        params_b=0, local=False, price_in_per_mtok=0.02, price_out_per_mtok=0.0
    )
    client = OpenAICompatibleLLMClient(
        base_url=settings.llm_tier1_base_url,
        api_key=settings.llm_tier1_api_key,
        model="text-embedding-3-small",
        timeout_seconds=30,
        priced_as=economics,
    )
    return client, "tier 1 endpoint"


async def main() -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    pairs = load_pairs(PAIRS)
    client, via = embedder()
    texts = sorted({p.said for p in pairs} | {o for p in pairs for o in p.options})
    vectors = dict(zip(texts, await client.embed(texts), strict=True))
    similarities = [{o: cosine(vectors[p.said], vectors[o]) for o in p.options} for p in pairs]
    judged = judge(pairs, lambda p: ungrounded_choice(p.option, [p.said]) is None, similarities)
    rows = sweep(judged, MARGINS)
    best = recommend(judged)
    chosen = None if best is None else sweep(judged, [best.margin])[0]

    print(f"{'said':<46} {'option':<34} {'label':<9} word  sim    margin")
    for j in judged:
        label = "yes" if j.pair.supported else "no"
        word = "yes" if j.word_supported else "no"
        print(f"{j.pair.said[:44]:<46} {j.pair.option[:32]:<34} {label:<9} {word:<5} ", end="")
        print(f"{j.similarity:.3f}  {j.margin:+.3f}")
    word_accepts = sum(1 for j in judged if not j.pair.supported and j.word_supported)
    word_refusals = sum(1 for j in judged if j.pair.supported and not j.word_supported)
    print(f"\nword check alone, {len(judged)} pairs: ", end="")
    print(f"{word_accepts} false accepts, {word_refusals} false refusals")
    if best is None or chosen is None:
        print("no margin stays above every refused negative while accepting a real answer")
    else:
        print(f"recommended margin {best.margin}: ", end="")
        print(f"{chosen.false_accepts} false accepts, {chosen.false_refusals} false refusals")
        print(f"headroom: highest refused negative {best.highest_negative:+.4f}, ", end="")
        print(f"lowest accepted real answer {best.lowest_positive:+.4f}")

    report = {
        "measured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": client.model,
        "via": via,
        "pairs": len(judged),
        "negatives": sum(1 for j in judged if not j.pair.supported),
        "word_check": {"false_accepts": word_accepts, "false_refusals": word_refusals},
        "recommended_margin": None if best is None else best.margin,
        "headroom": (
            None
            if best is None
            else {
                "highest_negative": round(best.highest_negative, 4),
                "lowest_positive": round(best.lowest_positive, 4),
            }
        ),
        "at_recommended": (
            None
            if chosen is None
            else {"false_accepts": chosen.false_accepts, "false_refusals": chosen.false_refusals}
        ),
        "judged": [
            {
                "said": j.pair.said,
                "option": j.pair.option,
                "options": list(j.pair.options),
                "language": j.pair.language,
                "supported": j.pair.supported,
                "word_supported": j.word_supported,
                "similarity": round(j.similarity, 4),
                "margin": round(j.margin, 4),
            }
            for j in judged
        ],
        "sweep": [
            {
                "margin": r.margin,
                "false_accepts": r.false_accepts,
                "false_refusals": r.false_refusals,
            }
            for r in rows
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"written to {REPORT.relative_to(BACKEND)}")


if __name__ == "__main__":
    asyncio.run(main())
