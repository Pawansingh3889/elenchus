#!/usr/bin/env python3
# Only repositories may build queries: no select/func/selectinload above that layer.
"""No ORM query surface above the repository layer (CLAUDE.md, layering).

Read the rule precisely. A router names ``AsyncSession`` to declare the FastAPI
dependency and a service takes one to own the transaction; neither is a query.
What must not travel upward is the query surface itself, because that is the
shortcut that quietly turns a service into a repository and leaves the data
access for one endpoint somewhere nobody thinks to look.

This is a guard rather than an import-linter contract because the distinction is
below module granularity: ``sqlalchemy.ext.asyncio`` is allowed and ``sqlalchemy
.select`` is not, and import-linter cannot forbid a subpackage of an external
package. So the check is on names, via the AST, which is also what lets it catch
``import sqlalchemy`` followed by ``sqlalchemy.select(...)``.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

from _guard import repo_root, report, require_paths

# Names that build or shape a query. Importing any of these above a repository
# means that layer is doing data access.
QUERY_NAMES = frozenset(
    {
        "select",
        "insert",
        "update",
        "delete",
        "func",
        "text",
        "Row",
        "join",
        "union",
        "exists",
        "selectinload",
        "joinedload",
        "subqueryload",
        "aliased",
    }
)

# Modules whose every name is query surface, whatever it is called.
QUERY_MODULES = frozenset({"sqlalchemy.orm", "sqlalchemy.sql"})

# The layers above the repository. models.py is excluded: a model *is* the
# schema and declares columns with sqlalchemy types by definition.
CHECKED_LAYERS = ("router.py", "service.py", "generation.py", "engine.py", "summary.py")


def violations_in(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in QUERY_MODULES:
                names = ", ".join(a.name for a in node.names)
                found.append(f"{path}:{node.lineno}: imports {names} from {module}")
            elif module == "sqlalchemy":
                bad = sorted({a.name for a in node.names} & QUERY_NAMES)
                if bad:
                    found.append(f"{path}:{node.lineno}: imports {', '.join(bad)} from sqlalchemy")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                # A bare `import sqlalchemy` puts the whole surface in reach, and
                # the attribute access that follows is not an import to catch.
                if alias.name == "sqlalchemy" or alias.name in QUERY_MODULES:
                    found.append(f"{path}:{node.lineno}: imports {alias.name} wholesale")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    args = parser.parse_args()

    app = args.root / "app"
    require_paths([app], "app/ package")

    targets = sorted(p for p in app.rglob("*.py") if p.name in CHECKED_LAYERS)
    require_paths(targets, f"any of {', '.join(CHECKED_LAYERS)} under app/")

    violations: list[str] = []
    for path in targets:
        violations.extend(violations_in(path))
    return report("no query surface above the repository layer", violations, len(targets))


if __name__ == "__main__":
    raise SystemExit(main())
