#!/usr/bin/env python3
# Prompts are code: every prompt file is versioned, and every version loaded exists.
"""Prompts as code, loaded by name and version (CLAUDE.md).

Two failures this catches, both of which have a long fuse.

An unversioned prompt file means editing it silently changes the behaviour of
every run already recorded against it, and a stored ``prompt_version`` that
cannot be resolved back to a file is a record of nothing.

A ``PROMPT_VERSION`` constant naming a file that does not exist fails at the
moment a model is called, which in this codebase is the one path that costs
money and cannot be exercised by the mocked suite. Better here, for free.
"""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path

from _guard import repo_root, report, require_paths

VERSIONED = re.compile(r"^[a-z0-9_]+_v\d+\.md$")

# Constants whose value must name a prompt file. Named rather than inferred, so
# adding a new one is a deliberate act.
PROMPT_CONSTANTS = ("PROMPT_VERSION", "VERIFY_PROMPT_VERSION")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    args = parser.parse_args()

    prompts_dir = args.root / "app" / "llm" / "prompts"
    app = args.root / "app"
    require_paths([prompts_dir], "app/llm/prompts/")

    prompts = sorted(prompts_dir.glob("*.md"))
    require_paths(prompts, "any .md prompt under app/llm/prompts/")
    available = {p.stem for p in prompts}

    violations = [
        f"{p}: filename is not <name>_v<N>.md" for p in prompts if not VERSIONED.match(p.name)
    ]

    # Every PROMPT_VERSION constant must name a file that is actually there.
    sources = sorted(app.rglob("*.py"))
    for path in sources:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if not any(n in PROMPT_CONSTANTS for n in names):
                continue
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                wanted = node.value.value
                if wanted not in available:
                    violations.append(
                        f"{path}:{node.lineno}: {names[0]} = {wanted!r}, "
                        f"but app/llm/prompts/{wanted}.md does not exist"
                    )

    return report("prompts are versioned and resolvable", violations, len(prompts))


if __name__ == "__main__":
    raise SystemExit(main())
