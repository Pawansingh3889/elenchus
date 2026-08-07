#!/usr/bin/env python3
# The schema comes from Alembic only: no metadata.create_all anywhere in app code.
"""Alembic owns the schema. No ``create_all`` in application code (CLAUDE.md).

``Base.metadata.create_all()`` is the shortcut that makes a fresh database work
without running migrations, and it is precisely why it must not exist here. Once
one environment gets its schema from the models and another from the migrations,
the two drift silently, and the first anyone hears of it is a column that exists
in development and not in production.

Tests are checked too. A suite that builds its schema from the models is testing
the models rather than the migrations, so a migration that fails to apply stays
green until deployment.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

from _guard import repo_root, report, require_paths


def violations_in(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        # Any *reference* to the attribute, not only a direct call. The async idiom
        # passes the bound method instead of calling it, as in
        # conn.run_sync(Base.metadata.create_all), and builds the schema just as
        # surely; while only ast.Call was checked, this repository's own conftest sat
        # in the blind spot and the gate reported ok over the exact violation it
        # exists to forbid. An Attribute node also covers the direct call, whose func
        # is this same node.
        if isinstance(node, ast.Attribute) and node.attr in {"create_all", "drop_all"}:
            found.append(f"{path}:{node.lineno}: references {node.attr}")
        # `from sqlalchemy.schema import CreateTable` style reach-arounds.
        elif isinstance(node, ast.ImportFrom) and node.module == "sqlalchemy.schema":
            names = sorted(a.name for a in node.names if a.name in {"CreateTable", "DropTable"})
            if names:
                found.append(f"{path}:{node.lineno}: imports {', '.join(names)}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    args = parser.parse_args()

    roots = require_paths([args.root / "app", args.root / "tests"], "app/ and tests/")
    targets = sorted(p for root in roots for p in root.rglob("*.py"))
    require_paths(targets, "any Python file under app/ or tests/")

    violations: list[str] = []
    for path in targets:
        violations.extend(violations_in(path))
    return report("no create_all outside Alembic", violations, len(targets))


if __name__ == "__main__":
    raise SystemExit(main())
