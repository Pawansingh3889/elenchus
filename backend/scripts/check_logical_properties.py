#!/usr/bin/env python3
# CSS must stay direction-agnostic: no margin-left and friends, so RTL keeps working.
"""No physical left/right CSS, so the layout mirrors for right-to-left languages.

The app ships in Arabic, Hebrew and Urdu, where the whole layout reads the other
way round. `margin-left` is a promise about the screen; `margin-inline-start` is a
promise about the reading order, and only the second one survives a change of
direction.

This is a guard rather than a review habit because the failure is invisible in
development: everything looks right in English, and the first person to see the
broken version is a reader in Arabic. One `padding-left` added months from now
puts an indent on the wrong side of exactly one component, which is the kind of
thing nobody files a bug about.

`border-radius`'s four-value shorthand is caught too. It runs top-left,
top-right, bottom-right, bottom-left, so a rounded corner paired with an accent
border ends up on the opposite edge from the border once the page flips.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from _guard import repo_root, report, require_paths

# (pattern, what to use instead)
FORBIDDEN: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bmargin-(left|right)\s*:"), "margin-inline-start / margin-inline-end"),
    (re.compile(r"\bpadding-(left|right)\s*:"), "padding-inline-start / padding-inline-end"),
    (re.compile(r"\bborder-(left|right)\s*:"), "border-inline-start / border-inline-end"),
    (
        re.compile(r"\bborder-(top|bottom)-(left|right)-radius\s*:"),
        "border-start-start-radius and friends",
    ),
    (re.compile(r"\btext-align\s*:\s*(left|right)\b"), "text-align: start / end"),
    (re.compile(r"^\s*(left|right)\s*:"), "inset-inline-start / inset-inline-end"),
)

# A four-value border-radius is positional and therefore physical.
FOUR_VALUE_RADIUS = re.compile(r"\bborder-radius\s*:\s*[^;]*?\s+\S+\s+\S+\s+\S+\s*;")


def violations_in(path: Path) -> list[str]:
    found: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        # A line that says so explicitly is a considered exception, not an oversight.
        if "logical-ok" in line:
            continue
        for pattern, instead in FORBIDDEN:
            if pattern.search(line):
                found.append(f"{path}:{number}: {line.strip()}  ->  use {instead}")
        if FOUR_VALUE_RADIUS.search(line):
            found.append(
                f"{path}:{number}: {line.strip()}  ->  four-value border-radius is "
                "positional; use the border-start-start-radius family"
            )
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "frontend",
    )
    args = parser.parse_args()

    require_paths([args.root], f"frontend at {args.root}")
    # Source only. Build output is generated, minified onto one line, and rewritten by
    # the bundler, so scanning it reports faults nobody wrote and cannot fix.
    skip = {"node_modules", ".next", "dist", "build", "out", "coverage"}
    sheets = sorted(
        p
        for p in args.root.rglob("*.css")
        if not (skip & set(p.parts)) and not any(part.startswith(".") for part in p.parts)
    )
    require_paths(sheets, f"any source .css under {args.root}")

    violations: list[str] = []
    for sheet in sheets:
        violations.extend(violations_in(sheet))
    return report("no physical left/right CSS", violations, len(sheets), unit="stylesheet")


if __name__ == "__main__":
    raise SystemExit(main())


# repo_root is imported for parity with the other guards' --root default; the frontend
# lives beside the backend rather than inside it, so this one resolves from __file__.
_ = repo_root
