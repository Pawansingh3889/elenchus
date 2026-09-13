#!/usr/bin/env python3
# Prompts are code: every prompt file is versioned, and every version loaded exists.
"""Prompts as code, loaded by name and version (CLAUDE.md).

Two failures this catches, both of which have a long fuse.

An unversioned prompt file means editing it silently changes the behaviour of
every run already recorded against it, and a stored ``prompt_version`` that
cannot be resolved back to a file is a record of nothing.

A prompt name that does not resolve to a file fails at the moment a model is
called, which in this codebase is the one path that costs money and cannot be
exercised by the mocked suite. Better here, for free.

Both ways of naming one are checked. A ``PROMPT_VERSION`` constant is the form
this guard was written for, but three call sites name their prompt inline as
``load_prompt("conduct_v3")``, and those were invisible to it: renaming
``conduct_v3.md`` left the gate green and broke every respondent turn.
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
PROMPT_CONSTANTS = (
    "PROMPT_VERSION",
    "VERIFY_PROMPT_VERSION",
    "GENERATE_PROMPT_VERSION",
    "REFINE_PROMPT_VERSION",
    "JUDGE_PROMPT_VERSION",
)

# The loader itself. A literal argument names a prompt just as surely as a constant
# does, and is the form the three engine and generation call sites use.
LOADER = "load_prompt"


def _wanted_prompt(node: ast.AST) -> tuple[str, str] | None:
    """The prompt name this node asks for, with the label to report it under.

    ``None`` for anything that does not name one outright: ``load_prompt(PROMPT_VERSION)``
    passes a variable, and the constant it reads is checked in its own right.
    """
    if isinstance(node, ast.Assign):
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        target = next((n for n in names if n in PROMPT_CONSTANTS), None)
        if target and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return target, node.value.value
        return None

    if isinstance(node, ast.Call) and node.args:
        func = node.func
        called = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
        first = node.args[0]
        if called == LOADER and isinstance(first, ast.Constant) and isinstance(first.value, str):
            return f"{LOADER}()", first.value
    return None


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

    # Every prompt named in the source, by constant or by literal, must be on disk.
    sources = sorted(app.rglob("*.py"))
    for path in sources:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            named = _wanted_prompt(node)
            if named is None:
                continue
            label, wanted = named
            if wanted not in available:
                violations.append(
                    f"{path}:{node.lineno}: {label} names {wanted!r}, "
                    f"but app/llm/prompts/{wanted}.md does not exist"
                )

    return report("prompts are versioned and resolvable", violations, len(prompts))


if __name__ == "__main__":
    raise SystemExit(main())
