#!/usr/bin/env python3
# Text colours must stay readable: contrast is arithmetic, so it is checked, not eyeballed.
"""WCAG contrast floors for the palette in frontend/app/globals.css.

Colour contrast is the one design property that is a calculation rather than a
matter of taste, which makes it the one worth a gate. This repository shipped
`--muted` at 2.65:1 against a 4.5:1 requirement, on text reading "No templates
yet. Create one or draft with AI.", and nothing anywhere said so.

The pairs below are checked because each is a colour actually painted on that
background in the stylesheet. A token that is never text (``--muted-light``, which
draws borders and the typing dots) is deliberately absent: holding decoration to a
text threshold would force a redesign to satisfy a rule that does not apply to it.

Thresholds are WCAG 2.1 AA: 4.5:1 for body text, 3:1 for a focus indicator or any
other non-text control boundary.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from _guard import fail, report, require_paths

# (foreground token, background token, minimum ratio, what it is)
PAIRS: tuple[tuple[str, str, float, str], ...] = (
    ("muted", "raised", 4.5, "muted text on a card"),
    ("muted", "surface", 4.5, "muted text on a field"),
    ("muted", "canvas", 4.5, "muted text on the page background"),
    ("secondary", "raised", 4.5, "secondary text on a card"),
    ("accent-strong", "raised", 4.5, "card labels"),
    ("ink", "canvas", 4.5, "body text"),
    # The top bar and primary button. Added after a dark theme turned the bar light
    # while its text stayed light, because --ink was painting both body text and the
    # slab: one token, two jobs, and they diverge the moment a second theme exists.
    ("on-slab", "slab", 4.5, "text on the top bar"),
    ("err-text", "err-fill", 4.5, "error text on its fill"),
    ("warn-text", "warn-fill", 4.5, "warning text on its fill"),
    ("focus", "raised", 3.0, "focus ring on a card"),
    ("focus", "canvas", 3.0, "focus ring on the page background"),
)

TOKEN = re.compile(r"^\s*--([a-z0-9-]+):\s*(#[0-9a-fA-F]{3,8})\s*;", re.MULTILINE)
# A palette block is a selector followed by declarations. Splitting on these rather
# than reading the file flat is the whole point: a flat read takes the last definition
# of each token, so the moment a dark theme was added the guard would have quietly
# stopped checking the light one and reported success either way.
BLOCK = re.compile(r"(?P<selector>[^{}]+)\{(?P<body>[^{}]*)\}")


def _luminance(value: str) -> float:
    hexed = value.lstrip("#")
    if len(hexed) == 3:
        hexed = "".join(c * 2 for c in hexed)
    channels = [int(hexed[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(foreground: str, background: str) -> float:
    a, b = _luminance(foreground), _luminance(background)
    high, low = max(a, b), min(a, b)
    return (high + 0.05) / (low + 0.05)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stylesheet",
        type=Path,
        # Resolved from this file so the guard works from any working directory.
        default=Path(__file__).resolve().parents[2] / "frontend" / "app" / "globals.css",
    )
    args = parser.parse_args()

    require_paths([args.stylesheet], f"stylesheet at {args.stylesheet}")
    text = args.stylesheet.read_text(encoding="utf-8")

    # The base palette, then every override that redefines it. A theme is checked as
    # base-overlaid-with-override, which is exactly how the browser resolves it.
    base: dict[str, str] = {}
    themes: dict[str, dict[str, str]] = {}
    for block in BLOCK.finditer(text):
        selector = re.sub(r"/\*.*?\*/", "", block.group("selector"), flags=re.S)
        selector = " ".join(selector.split())
        tokens = dict(TOKEN.findall(block.group("body")))
        if not tokens:
            continue
        if selector == ":root":
            base.update(tokens)
        elif "data-theme" in selector or "prefers-color-scheme" in selector:
            themes.setdefault(selector, {}).update(tokens)

    if not base:
        fail(
            f"no :root palette found in {args.stylesheet}.",
            "The palette moved or changed shape, so this guard is checking nothing.",
        )

    palettes = {"light": base}
    for selector, overrides in themes.items():
        palettes[selector] = {**base, **overrides}

    violations: list[str] = []
    for name, tokens in palettes.items():
        for fg, bg, minimum, what in PAIRS:
            if fg not in tokens or bg not in tokens:
                # A renamed token silently drops its pair, which is how a check quietly
                # stops checking. Say so instead.
                violations.append(f"[{name}] {what}: --{fg} or --{bg} is no longer defined")
                continue
            ratio = contrast(tokens[fg], tokens[bg])
            if ratio < minimum:
                violations.append(
                    f"[{name}] {what}: --{fg} ({tokens[fg]}) on --{bg} ({tokens[bg]}) "
                    f"is {ratio:.2f}:1, needs {minimum}:1"
                )

    checked = len(PAIRS) * len(palettes)
    return report("palette contrast", violations, checked, unit="colour pair")


if __name__ == "__main__":
    raise SystemExit(main())
