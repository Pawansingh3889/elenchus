"""Answer accuracy from the captured live-run corpus, grouped by answer type.

Reads ``backend/tests/live_runs/*.json``, the same fixtures ``scripts/eval_report.py``
ratchets against on every push. This is offline judgement over captured
conversations, not live production traffic: the judge does not run against real
respondent answers today, only against this corpus, at gate time. A number here
describes the corpus, not this week's respondents.

Deliberately independent of ``scripts/eval_report.py`` rather than importing it: that
script is a CLI tool with its own argument parsing and ratchet-failure exit codes,
sibling to ``_guard`` and ``conduct_invariants`` under ``scripts/``, and importing a
script into the app the app is not one of the two readers ``ledger.py`` documents.
This owns only the counting, at the same field names, so the two cannot silently
disagree about what "judged" or "flagged" means.
"""

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.llm.schemas import EvalAccuracyReport, EvalAnswerTypeStats

# backend/app/llm/eval_corpus.py -> backend/app/llm -> backend/app -> backend
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
LIVE_RUNS_DIR = _BACKEND_ROOT / "tests" / "live_runs"


@dataclass
class _TypeBucket:
    total: int = 0
    judged: int = 0
    flagged: int = 0
    invented: int = 0


def _fixtures(live_runs: Path) -> list[dict[str, Any]]:
    out = []
    for path in sorted(live_runs.glob("*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return out


def get_eval_accuracy_report(live_runs: Path | None = None) -> EvalAccuracyReport:
    live_runs = live_runs or LIVE_RUNS_DIR
    if not live_runs.exists():
        return EvalAccuracyReport(
            total_fixtures=0,
            total_answers=0,
            judged=0,
            flagged=0,
            known_inventions=0,
            by_answer_type=[],
        )

    fixtures = _fixtures(live_runs)
    answers = [a for f in fixtures for a in f.get("answers", [])]

    buckets: dict[str, _TypeBucket] = defaultdict(_TypeBucket)
    for a in answers:
        answer_type = a.get("answer_type") or "unknown"
        b = buckets[answer_type]
        b.total += 1
        verdict = a.get("judge", {}).get("supported")
        if verdict is not None:
            b.judged += 1
            if verdict is False:
                b.flagged += 1
        if a.get("invented"):
            b.invented += 1

    by_answer_type = [
        EvalAnswerTypeStats(
            answer_type=answer_type,
            total_answers=b.total,
            judged=b.judged,
            flagged=b.flagged,
            known_inventions=b.invented,
        )
        for answer_type, b in sorted(buckets.items(), key=lambda x: -x[1].total)
    ]

    return EvalAccuracyReport(
        total_fixtures=len(fixtures),
        total_answers=len(answers),
        judged=sum(b.judged for b in buckets.values()),
        flagged=sum(b.flagged for b in buckets.values()),
        known_inventions=sum(b.invented for b in buckets.values()),
        by_answer_type=by_answer_type,
    )
