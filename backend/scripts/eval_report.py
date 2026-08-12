#!/usr/bin/env python3
# The corpus, in numbers, with a ratchet on the facts that must not regress.
"""What the replay corpus covers, and what must not go backwards.

Of the 28 defects in docs/DEFECTS.md, exactly one says it was found by a test. Everything
else was found by a person reading a live conversation. That is not an argument against
reading conversations, it is the observation that there was no detection channel at all:
no number was tracked over time, so nothing could drop.

This prints the numbers, and fails the build on the ones that are facts.

**Facts ratchet.** The size of the corpus, the number of known inventions in it, and
whether every recorded trace still satisfies every engine invariant. Each is a count or a
yes/no with no judgement in it, and each can only go the wrong way through a mistake:
deleting fixtures, unmarking an invention, breaking the engine's sequencing.

**Judgement prints.** Probe rate, cost per run, how many answers a judge liked. Those move
for legitimate reasons all the time, and a threshold guessed before the numbers exist is
a red that turns on judgement, which is how people learn to ignore red. The repository
already made this call once, about the judge itself, and this follows it.

The baseline lives in tests/eval_baseline.json and is raised by hand, deliberately: it is
a claim about coverage, and it should cost somebody a moment's thought to make it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _guard import fail, repo_root, report, require_paths
from conduct_invariants import check_all


def _fixtures(live_runs: Path) -> list[tuple[str, dict[str, Any]]]:
    out = []
    for path in sorted(live_runs.glob("*.json")):
        try:
            out.append((path.stem, json.loads(path.read_text(encoding="utf-8"))))
        except json.JSONDecodeError as exc:
            fail(f"{path.name} is not readable JSON: {exc}")
    return out


def measure(fixtures: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    """Everything the report says, computed once so printing and ratcheting agree."""
    answers = [a for _, fixture in fixtures for a in fixture.get("answers", [])]
    traced = [(name, f["trace"]) for name, f in fixtures if isinstance(f.get("trace"), dict)]

    invariant_failures = [
        f"{name}: {check}" for name, trace in traced for check, ok, _ in check_all(trace) if not ok
    ]

    models = sorted({str(f.get("model", "unknown")) for _, f in fixtures})
    return {
        "fixtures": len(fixtures),
        "answers": len(answers),
        "known_inventions": sum(1 for a in answers if a.get("invented")),
        "traced_fixtures": len(traced),
        "invariant_failures": invariant_failures,
        # Judgement, printed only.
        "follow_up_answers": sum(1 for a in answers if a.get("kind") == "follow_up"),
        "judged": sum(1 for a in answers if a.get("judge", {}).get("supported") is not None),
        "judge_flagged": sum(1 for a in answers if a.get("judge", {}).get("supported") is False),
        "models": models,
        "unattributed": [name for name, f in fixtures if f.get("model") in (None, "", "unknown")],
    }


def _print(seen: dict[str, Any]) -> None:
    print("corpus")
    print(f"  fixtures                {seen['fixtures']}")
    print(f"  answers                 {seen['answers']}")
    print(f"  known inventions        {seen['known_inventions']}")
    print(f"  fixtures with a trace   {seen['traced_fixtures']}")
    print(f"  models                  {', '.join(seen['models']) or 'none'}")
    print("\njudgement (printed, never gating)")
    print(f"  follow-up answers       {seen['follow_up_answers']}")
    print(f"  judged by a model       {seen['judged']}")
    print(f"  judge flagged           {seen['judge_flagged']}")
    if seen["unattributed"]:
        # Not a failure: a fixture predating the provenance work genuinely cannot say.
        # Named anyway, because "unknown" is what the corpus says when it cannot answer
        # the one question it exists for the moment somebody swaps the model.
        print(f"\n  {len(seen['unattributed'])} fixture(s) name no model: ")
        for name in seen["unattributed"]:
            print(f"    {name}")


def ratchet(seen: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    """Only the facts. A count that fell, or an invariant that stopped holding."""
    violations = list(seen["invariant_failures"])
    for key in ("answers", "known_inventions", "traced_fixtures"):
        was, now = int(baseline.get(key, 0)), int(seen[key])
        if now < was:
            violations.append(f"{key} fell from {was} to {now}")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="write today's numbers back as the new floor, after you have read them",
    )
    args = parser.parse_args()

    live_runs = require_paths([args.root / "tests" / "live_runs"], "tests/live_runs/")[0]
    fixtures = _fixtures(live_runs)
    if not fixtures:
        fail(
            "tests/live_runs/ holds no fixtures, so there is no corpus to measure.",
            "Capture one with scripts/live_conversation.py.",
        )

    seen = measure(fixtures)
    _print(seen)

    baseline_path = args.root / "tests" / "eval_baseline.json"
    if args.update_baseline:
        floor = {k: seen[k] for k in ("answers", "known_inventions", "traced_fixtures")}
        baseline_path.write_text(json.dumps(floor, indent=2) + "\n", encoding="utf-8")
        print(f"\nbaseline written: {floor}")
        return 0

    if not baseline_path.exists():
        fail(
            f"{baseline_path.name} is missing, so nothing can be ratcheted against it.",
            "Write one with --update-baseline once you have read the numbers above.",
        )
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    print()
    return report("eval corpus ratchet", ratchet(seen, baseline), len(fixtures), "fixture")


if __name__ == "__main__":
    raise SystemExit(main())
