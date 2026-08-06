# Tests that every checker script really catches the mistake it exists to catch.
"""Prove every gate rejects a planted violation.

A guard that has never been observed to fail is decoration. Green output tells
you a script ran and printed something reassuring; it does not tell you the
script would have objected had there been anything to object to.

Each guard is put through three cases, and the third is the one that bites in
practice:

1. a clean fake repository passes, because a guard that fails on everything is
   equally useless;
2. exactly one planted violation is rejected with a non-zero exit;
3. a missing precondition **fails** rather than passing. This is the failure
   mode that hides: rename a directory and a naive checker reports success
   having examined nothing. ``scripts/_guard.py`` exists for it.

Adopted from the copernus project, whose Makefile puts it best: a gate that has
never been observed to reject anything is decoration.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
SCRIPTS = BACKEND / "scripts"

GUARDS = ("check_query_surface.py", "check_no_create_all.py", "check_prompts_versioned.py")

# check_contrast.py reads one stylesheet rather than a repository tree, so it takes
# --stylesheet instead of --root and is proven separately below.


def run_guard(script: str, root: Path) -> subprocess.CompletedProcess[str]:
    """Run a guard against a repository root, exactly as `make guards` does."""
    env = dict(os.environ, PYTHONPATH=str(SCRIPTS))
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    """A minimal well-formed backend. Each test breaks exactly one thing."""
    app = tmp_path / "app"
    (app / "templates").mkdir(parents=True)
    (app / "llm" / "prompts").mkdir(parents=True)
    (tmp_path / "tests").mkdir()

    # A router that names AsyncSession and nothing else from sqlalchemy: legal.
    (app / "templates" / "router.py").write_text(
        "from sqlalchemy.ext.asyncio import AsyncSession\n\n\nasync def read(s: AsyncSession):\n"
        "    return s\n",
        encoding="utf-8",
    )
    (app / "templates" / "service.py").write_text("VALUE = 1\n", encoding="utf-8")
    (app / "llm" / "prompts" / "conduct_v2.md").write_text("Be brief.\n", encoding="utf-8")
    (app / "runs.py").write_text('PROMPT_VERSION = "conduct_v2"\n', encoding="utf-8")
    (tmp_path / "tests" / "test_thing.py").write_text(
        "def test_ok():\n    assert True\n", encoding="utf-8"
    )
    return tmp_path


@pytest.mark.parametrize("guard", GUARDS)
def test_a_clean_repository_passes(guard: str, fake_repo: Path) -> None:
    """The floor. A guard that rejects everything proves nothing when it rejects."""
    result = run_guard(guard, fake_repo)
    assert result.returncode == 0, f"{guard} rejected a clean repo:\n{result.stderr}"
    assert result.stdout.startswith("ok:")


@pytest.mark.parametrize("guard", GUARDS)
def test_a_guard_fails_when_it_cannot_run(guard: str, tmp_path: Path) -> None:
    """The failure mode that hides: nothing to check must not read as success.

    Point each guard at an empty directory. A naive implementation walks no
    files, finds no violations, and exits 0 having verified nothing at all.
    """
    result = run_guard(guard, tmp_path)
    assert result.returncode != 0, f"{guard} passed with nothing to check:\n{result.stdout}"
    assert "cannot run" in result.stderr


# --------------------------------------------------------------- query surface


def test_query_surface_rejects_select_in_a_service(fake_repo: Path) -> None:
    (fake_repo / "app" / "templates" / "service.py").write_text(
        "from sqlalchemy import select\n\n\ndef q():\n    return select(1)\n", encoding="utf-8"
    )
    result = run_guard("check_query_surface.py", fake_repo)
    assert result.returncode == 1
    assert "imports select from sqlalchemy" in result.stderr


def test_query_surface_rejects_selectinload_in_a_router(fake_repo: Path) -> None:
    """The orm subpackage is entirely query surface, whatever the name."""
    (fake_repo / "app" / "templates" / "router.py").write_text(
        "from sqlalchemy.orm import selectinload\n", encoding="utf-8"
    )
    result = run_guard("check_query_surface.py", fake_repo)
    assert result.returncode == 1
    assert "sqlalchemy.orm" in result.stderr


def test_query_surface_rejects_a_wholesale_import(fake_repo: Path) -> None:
    """`import sqlalchemy` then `sqlalchemy.select(...)` is the same rule broken
    by a route the import-name check alone would miss."""
    (fake_repo / "app" / "templates" / "service.py").write_text(
        "import sqlalchemy\n\n\ndef q():\n    return sqlalchemy.select(1)\n", encoding="utf-8"
    )
    result = run_guard("check_query_surface.py", fake_repo)
    assert result.returncode == 1
    assert "wholesale" in result.stderr


def test_query_surface_allows_asyncsession_above_a_repository(fake_repo: Path) -> None:
    """The rule is about queries, not about the session travelling upward. If
    this ever fails, the guard has become stricter than the architecture."""
    (fake_repo / "app" / "templates" / "service.py").write_text(
        "from sqlalchemy.ext.asyncio import AsyncSession\n"
        "from sqlalchemy.exc import IntegrityError\n\n\n"
        "async def save(s: AsyncSession):\n"
        "    try:\n        await s.commit()\n    except IntegrityError:\n        raise\n",
        encoding="utf-8",
    )
    assert run_guard("check_query_surface.py", fake_repo).returncode == 0


# ---------------------------------------------------------------- create_all


def test_create_all_is_rejected_in_app_code(fake_repo: Path) -> None:
    (fake_repo / "app" / "templates" / "service.py").write_text(
        "async def init(conn, Base):\n    await conn.run_sync(Base.metadata.create_all)\n"
        "    Base.metadata.create_all(bind=conn)\n",
        encoding="utf-8",
    )
    result = run_guard("check_no_create_all.py", fake_repo)
    assert result.returncode == 1
    assert "create_all" in result.stderr


def test_create_all_is_rejected_in_tests_too(fake_repo: Path) -> None:
    """A suite that builds its schema from the models is not testing the
    migrations, so a migration that cannot apply stays green until deployment."""
    (fake_repo / "tests" / "test_thing.py").write_text(
        "def test_schema(engine, Base):\n    Base.metadata.create_all(engine)\n", encoding="utf-8"
    )
    result = run_guard("check_no_create_all.py", fake_repo)
    assert result.returncode == 1


# ------------------------------------------------------------------- prompts


def test_an_unversioned_prompt_is_rejected(fake_repo: Path) -> None:
    (fake_repo / "app" / "llm" / "prompts" / "conduct.md").write_text("Hi.\n", encoding="utf-8")
    result = run_guard("check_prompts_versioned.py", fake_repo)
    assert result.returncode == 1
    assert "not <name>_v<N>.md" in result.stderr


def test_a_prompt_version_naming_no_file_is_rejected(fake_repo: Path) -> None:
    """The failure this replaces happens at the moment a model is called, which
    is the one path the mocked suite cannot exercise."""
    (fake_repo / "app" / "runs.py").write_text('PROMPT_VERSION = "conduct_v9"\n', encoding="utf-8")
    result = run_guard("check_prompts_versioned.py", fake_repo)
    assert result.returncode == 1
    assert "does not exist" in result.stderr


# ------------------------------------------------------- the contracts themselves


def test_import_contracts_hold() -> None:
    """`lint-imports` on the real package, so `make gate` is not the only place
    the layering is checked and a broken contract fails the suite too."""
    lint_imports = Path(sys.executable).parent / "lint-imports"
    if not lint_imports.exists():
        pytest.fail(f"lint-imports is not installed at {lint_imports}; this gate cannot run")
    result = subprocess.run(
        [str(lint_imports)], cwd=BACKEND, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


# ------------------------------------------------------------------- contrast


def run_contrast(stylesheet: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(SCRIPTS))
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "check_contrast.py"), "--stylesheet", str(stylesheet)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


PALETTE = """:root {{
  --ink: #23262b;
  --canvas: #eceef0;
  --surface: #f7f8f9;
  --white: #ffffff;
  --muted: {muted};
  --secondary: #636b73;
  --accent-strong: #3c5570;
  --focus: {focus};
  --warn-fill: #fdf3d9;
  --warn-text: #7a4a06;
  --err-fill: #fadbd5;
  --err-text: #8a2c18;
}}
"""


def test_an_accessible_palette_passes(tmp_path: Path) -> None:
    sheet = tmp_path / "globals.css"
    sheet.write_text(PALETTE.format(muted="#646d76", focus="#4190c2"), encoding="utf-8")
    result = run_contrast(sheet)
    assert result.returncode == 0, result.stderr
    assert "colour pair" in result.stdout


def test_the_grey_this_repo_actually_shipped_is_rejected(tmp_path: Path) -> None:
    """#98a0a8 was the real value, on real sentences, at 2.65:1. If this guard would
    not have caught it, it is not worth running."""
    sheet = tmp_path / "globals.css"
    sheet.write_text(PALETTE.format(muted="#98a0a8", focus="#4190c2"), encoding="utf-8")
    result = run_contrast(sheet)
    assert result.returncode == 1
    assert "2.65:1" in result.stderr


def test_a_focus_ring_below_three_to_one_is_rejected(tmp_path: Path) -> None:
    """The old focus colour, --accent at 1.81:1, which is why focus was invisible."""
    sheet = tmp_path / "globals.css"
    sheet.write_text(PALETTE.format(muted="#646d76", focus="#9ec6e0"), encoding="utf-8")
    result = run_contrast(sheet)
    assert result.returncode == 1
    assert "focus ring" in result.stderr


def test_a_renamed_token_is_a_violation_not_a_silent_pass(tmp_path: Path) -> None:
    """Dropping a pair because its token vanished is how a check stops checking."""
    sheet = tmp_path / "globals.css"
    sheet.write_text(
        PALETTE.format(muted="#646d76", focus="#4190c2").replace("--focus:", "--ring:"),
        encoding="utf-8",
    )
    result = run_contrast(sheet)
    assert result.returncode == 1
    assert "no longer defined" in result.stderr


def test_contrast_fails_when_it_cannot_run(tmp_path: Path) -> None:
    assert run_contrast(tmp_path / "absent.css").returncode != 0


def test_a_stylesheet_with_no_tokens_fails(tmp_path: Path) -> None:
    """An empty file has no failing pairs, which must not read as success."""
    sheet = tmp_path / "globals.css"
    sheet.write_text("body { color: red; }\n", encoding="utf-8")
    result = run_contrast(sheet)
    assert result.returncode == 1
    assert "checking nothing" in result.stderr
