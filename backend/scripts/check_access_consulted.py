#!/usr/bin/env python3
# Survey data may not leave a service without app/access being consulted.
"""No survey, run or answer leaves a service without asking app/access (CLAUDE.md).

The mistake this exists to catch is not a wrong rule. It is a new endpoint whose
service method simply never asks, which no amount of care in `app/access` prevents
and which no reviewer reliably notices, because the missing line is invisible: the
method looks complete, returns the right type, and hands another department's
survey to whoever called it.

So the check is blunt on purpose. A public service method whose return type
mentions survey data must, somewhere in its body, call one of the access rules.
It does not verify the rule was applied *correctly*, which is what
tests/test_access_rules.py is for. It verifies the question was asked at all.

Exemptions are deliberate and self-documenting: put ``access-exempt: <reason>`` in
the method's docstring. That keeps the reason next to the code rather than in a
list somewhere, and makes an exemption something you write a sentence to justify.
A bare marker with no reason is itself a violation, because "exempt" with no
argument is how a rule quietly stops applying.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

from _guard import repo_root, report, require_paths

# Where business logic lives. app/conduct puts its logic in engine.py rather than a
# service.py, which the layering contract already documents as deliberate, so the
# guard follows the code rather than the filename convention.
CHECKED_FILES = frozenset({"service.py", "engine.py", "summary.py"})

# A return annotation mentioning any of these is survey data leaving the layer.
# Model classes and the read schemas built from them, because a leak through a
# Pydantic model is exactly as bad as one through an ORM row.
GUARDED_TYPES = frozenset(
    {
        "SurveyTemplate",
        "SurveyTemplateVersion",
        "SurveyRun",
        "Answer",
        "TemplateRead",
        "TemplateSummary",
        "GeneratedTemplate",
        "RunDetail",
        "RunSummary",
        "DashboardRow",
        "ResultRow",
        # The most attribution-dense payload in the API: every answer in the survey with
        # the respondent beside it, which is exactly what must not leak to a colleague.
        "AnswersMatrix",
        # The trace: refusal reasons can quote a value a model proposed from a respondent's
        # words, so the lens reads are held to the same rule as the results they explain.
        "TracedRun",
        "SpanRead",
        "LensStrip",
        "AttemptRow",
        "DecisionRow",
        "CorrelationMatrix",
        # What respondents typed, placed by meaning.
        "AnswerMap",
        "ThemeReport",
        "DuplicateReport",
        # What respondents typed, read by a local model.
        "CapturedAsk",
        "StoredAnalysis",
        # Recorded answers beside what respondents said, labelled and judged.
        "EvalItem",
        "FaithfulnessReport",
        "JudgeRunRead",
        "QualityReport",
        "EvalRunRead",
    }
)

ACCESS_RULES = frozenset(
    {"may_answer", "may_list", "may_read_rows", "may_read_totals", "is_admin", "may_edit"}
)

EXEMPT = "access-exempt:"


def _annotation_names(node: ast.expr | None) -> set[str]:
    """Every bare name in a return annotation, however it is nested.

    `list[tuple[SurveyTemplate, int]]` has to be caught as surely as `SurveyTemplate`:
    wrapping the return value in a container does not make it less of a leak.
    """
    if node is None:
        return set()
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            names.add(child.id)
        elif isinstance(child, ast.Attribute):
            names.add(child.attr)
        elif isinstance(child, ast.Constant) and isinstance(child.value, str):
            # A string annotation, from `from __future__ import annotations` or a
            # forward reference. Parse it rather than skip it.
            try:
                names |= _annotation_names(ast.parse(child.value, mode="eval").body)
            except SyntaxError:
                names.add(child.value)
    return names


def _called_names(func: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        target = node.func
        name = target.attr if isinstance(target, ast.Attribute) else getattr(target, "id", None)
        if isinstance(name, str):
            names.add(name)
    return names


def _private_functions(tree: ast.AST) -> dict[str, ast.AST]:
    return {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("_")
    }


def _consults_access(func: ast.AST, helpers: dict[str, ast.AST], seen: frozenset[str]) -> bool:
    """Whether this function asks, directly or through a private helper beside it.

    Following the helpers matters because that is how these services are actually
    written: `_get_or_404` and `_owned_or_404` are where ownership is settled, and
    every public method leans on them. A guard blind to that would demand the check
    be inlined into a dozen methods, or, far more likely, would teach people to
    write an exemption whenever it complained. Either way it stops meaning anything.

    Only private helpers in the same module, and only ones seen once, so a pair of
    mutually recursive helpers cannot spin.
    """
    called = _called_names(func)
    if called & ACCESS_RULES:
        return True
    for name in called & helpers.keys():
        if name in seen:
            continue
        if _consults_access(helpers[name], helpers, seen | {name}):
            return True
    return False


def _exemption(func: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """The stated reason this method is exempt, or None if it claims no exemption."""
    doc = ast.get_docstring(func) or ""
    if EXEMPT not in doc:
        return None
    return doc.split(EXEMPT, 1)[1].strip()


def violations_in(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    helpers = _private_functions(tree)
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # Private helpers are reached through a public method that was already
        # checked; requiring the question twice would only teach people to inline.
        if node.name.startswith("_"):
            continue
        if not (_annotation_names(node.returns) & GUARDED_TYPES):
            continue

        reason = _exemption(node)
        if reason is not None:
            if not reason:
                found.append(
                    f"{path}:{node.lineno}: {node.name} is marked {EXEMPT} with no reason given"
                )
            continue
        if not _consults_access(node, helpers, frozenset()):
            found.append(
                f"{path}:{node.lineno}: {node.name} returns survey data without consulting "
                f"app/access (call one of {', '.join(sorted(ACCESS_RULES))}, or document "
                f"'{EXEMPT} <reason>' in its docstring)"
            )
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=repo_root())
    args = parser.parse_args()

    app = args.root / "app"
    require_paths([app], "app/ package")

    targets = sorted(p for p in app.rglob("*.py") if p.name in CHECKED_FILES)
    require_paths(targets, f"any of {', '.join(sorted(CHECKED_FILES))} under app/")

    violations: list[str] = []
    for path in targets:
        violations.extend(violations_in(path))
    return report("survey data never leaves a service unchecked", violations, len(targets))


if __name__ == "__main__":
    raise SystemExit(main())
