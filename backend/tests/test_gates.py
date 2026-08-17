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

Adopted from a sibling project, whose Makefile puts it best: a gate that has
never been observed to reject anything is decoration.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
SCRIPTS = BACKEND / "scripts"

GUARDS = (
    "check_query_surface.py",
    "check_access_consulted.py",
    "check_no_create_all.py",
    "check_prompts_versioned.py",
)

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
        "async def init(conn, Base):\n    Base.metadata.create_all(bind=conn)\n",
        encoding="utf-8",
    )
    result = run_guard("check_no_create_all.py", fake_repo)
    assert result.returncode == 1
    assert "create_all" in result.stderr


def test_create_all_passed_to_run_sync_is_rejected_on_its_own(fake_repo: Path) -> None:
    """The async idiom hands the bound method to run_sync instead of calling it, and
    builds the schema just as surely. Planted ALONE, because the old planted violation
    paired it with a direct call: the guard caught the pair for the wrong reason, and
    this repository's own conftest sat in the blind spot while the gate reported ok."""
    (fake_repo / "app" / "templates" / "service.py").write_text(
        "async def init(conn, Base):\n    await conn.run_sync(Base.metadata.create_all)\n",
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


def test_a_prompt_named_inline_at_the_call_site_is_rejected(fake_repo: Path) -> None:
    """A constant is not the only way to name a prompt, and it is not the way the
    engine names its own: load_prompt("conduct_v4") is a literal. Those call sites sat
    outside this guard entirely, so renaming the file left the gate green and broke
    every respondent turn at the one moment that costs money to discover."""
    (fake_repo / "app" / "conduct.py").write_text(
        "from app.llm.prompts import load_prompt\n\n"
        'def decide():\n    return load_prompt("conduct_v9")\n',
        encoding="utf-8",
    )
    result = run_guard("check_prompts_versioned.py", fake_repo)
    assert result.returncode == 1
    assert "does not exist" in result.stderr


@pytest.mark.parametrize("name", ["GENERATE_PROMPT_VERSION", "REFINE_PROMPT_VERSION"])
def test_the_generation_constants_are_checked_like_every_other(fake_repo: Path, name: str) -> None:
    """Hoisting a literal into a constant must not be how a call site leaves the guard.

    `load_prompt("generate_template_v4")` was checked because it was a literal. Naming it
    `GENERATE_PROMPT_VERSION` moved it out of the literal rule, and the guard recognises
    constants only by name, so a rename that did not also update PROMPT_CONSTANTS would
    have quietly stopped checking the drafting prompts altogether: green gate, and a
    generate that 500s the first time an author asks for one.
    """
    (fake_repo / "app" / "generation.py").write_text(
        f'{name} = "generate_template_v99"\n', encoding="utf-8"
    )
    result = run_guard("check_prompts_versioned.py", fake_repo)
    assert result.returncode == 1
    assert "does not exist" in result.stderr


def test_a_prompt_loaded_through_a_variable_is_left_to_the_constant_rule(
    fake_repo: Path,
) -> None:
    """load_prompt(PROMPT_VERSION) names nothing on its own. Flagging the variable as
    though it were a filename would fail the guard on the codebase's own summary
    service, whose constant is checked separately and resolves."""
    (fake_repo / "app" / "runs.py").write_text(
        "from app.llm.prompts import load_prompt\n\n"
        'PROMPT_VERSION = "conduct_v2"\n\n'
        "def write():\n    return load_prompt(PROMPT_VERSION)\n",
        encoding="utf-8",
    )
    result = run_guard("check_prompts_versioned.py", fake_repo)
    assert result.returncode == 0, result.stderr


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
  --raised: #ffffff;
  --slab: #23262b;
  --on-slab: #eceef0;
  --muted: {muted};
  --secondary: #636b73;
  --accent-strong: #3c5570;
  --focus: {focus};
  --warn-fill: #fdf3d9;
  --warn-text: #7a4a06;
  --err-fill: #fadbd5;
  --err-text: #8a2c18;
  --hero-from: #00417f;
  --hero-to: #0b6fb8;
  --on-hero: #ffffff;
  --on-hero-muted: #e8f1f8;
  --band-1: #e9edf3;
  --band-2: #d8dfe8;
  --band-3: #bfc8d5;
  --band-4: #96a3b5;
  --band-5: #5e6d83;
  --band-6: #2f3d52;
  --on-band-1: #0b1222;
  --on-band-2: #0b1222;
  --on-band-3: #0b1222;
  --on-band-4: #0b1222;
  --on-band-5: #ffffff;
  --on-band-6: #ffffff;
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


def test_an_opaque_short_hex_is_measured_not_crashed_on(tmp_path: Path) -> None:
    """#rgb and #rgba with full alpha are valid CSS; the guard used to crash on the
    4-digit form (int('', 16)) and silently strip nothing from the 8-digit one."""
    sheet = tmp_path / "globals.css"
    sheet.write_text(
        PALETTE.format(muted="#646d76", focus="#4190c2").replace("#23262b;", "#223f;", 1),
        encoding="utf-8",
    )
    result = run_contrast(sheet)
    assert result.returncode == 0, result.stderr


def test_a_translucent_colour_is_a_violation_not_a_pass(tmp_path: Path) -> None:
    """An 8-digit hex with alpha below 1 has no single contrast ratio: what the eye
    sees depends on what it is painted over. Ignoring the alpha would let a
    see-through text colour pass the gate at full strength."""
    sheet = tmp_path / "globals.css"
    sheet.write_text(
        PALETTE.format(muted="#646d7680", focus="#4190c2"),
        encoding="utf-8",
    )
    result = run_contrast(sheet)
    assert result.returncode == 1
    assert "alpha" in result.stderr


def test_contrast_fails_when_it_cannot_run(tmp_path: Path) -> None:
    assert run_contrast(tmp_path / "absent.css").returncode != 0


def test_a_stylesheet_with_no_tokens_fails(tmp_path: Path) -> None:
    """An empty file has no failing pairs, which must not read as success."""
    sheet = tmp_path / "globals.css"
    sheet.write_text("body { color: red; }\n", encoding="utf-8")
    result = run_contrast(sheet)
    assert result.returncode == 1
    assert "checking nothing" in result.stderr


def test_every_theme_is_measured_not_just_the_last_one(tmp_path: Path) -> None:
    """The trap this guard nearly fell into. Reading the file flat takes the last
    definition of each token, so adding a dark theme would have silently replaced the
    light palette and reported success on one theme while claiming to check the app."""
    sheet = tmp_path / "globals.css"
    sheet.write_text(
        PALETTE.format(muted="#646d76", focus="#4190c2") + """
:root[data-theme="dark"] {
  --canvas: #15171a;
  --surface: #1c1f24;
  --raised: #212429;
  --slab: #0f1114;
  --on-slab: #e6e8ea;
  --ink: #e6e8ea;
  --muted: #55606a;
  --secondary: #b3bcc5;
  --accent-strong: #a9c9e4;
  --focus: #6db3e8;
  --warn-fill: #39290b;
  --warn-text: #f0cf8a;
  --err-fill: #3a1a13;
  --err-text: #f4b3a3;
}
""",
        encoding="utf-8",
    )
    result = run_contrast(sheet)
    # The light palette is fine; the dark one's muted grey is too dark against its own
    # backgrounds. A flat read would have seen only the dark values and never compared
    # them against the light backgrounds, or vice versa.
    assert result.returncode == 1
    assert "data-theme" in result.stderr
    assert "[light]" not in result.stderr


# --------------------------------------------------------- logical properties


def run_logical(root: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, PYTHONPATH=str(SCRIPTS))
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "check_logical_properties.py"), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


@pytest.fixture
def fake_frontend(tmp_path: Path) -> Path:
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "globals.css").write_text(
        ".a { margin-inline-start: 4px; text-align: start; }\n", encoding="utf-8"
    )
    return tmp_path


def test_direction_agnostic_css_passes(fake_frontend: Path) -> None:
    result = run_logical(fake_frontend)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("css", "expected"),
    [
        (".a { margin-left: 4px; }", "margin-inline-start"),
        (".a { padding-right: 4px; }", "padding-inline-start"),
        (".a { border-left: 1px solid red; }", "border-inline-start"),
        (".a { text-align: left; }", "text-align: start"),
        (".a { border-top-left-radius: 4px; }", "border-start-start-radius"),
        (".a { border-radius: 0 4px 4px 0; }", "positional"),
    ],
)
def test_physical_css_is_rejected(fake_frontend: Path, css: str, expected: str) -> None:
    """Each of these looks correct in English and puts something on the wrong side in
    Arabic, which is why a reviewer reading the diff in English will not catch them."""
    (fake_frontend / "app" / "globals.css").write_text(css + "\n", encoding="utf-8")
    result = run_logical(fake_frontend)
    assert result.returncode == 1, result.stdout
    assert expected in result.stderr


def test_an_explicit_exception_is_honoured(fake_frontend: Path) -> None:
    """Some rules genuinely are physical. Marking one is a decision on the record; the
    alternative is that the first genuine exception disables the guard entirely."""
    (fake_frontend / "app" / "globals.css").write_text(
        ".a { margin-left: 4px; } /* logical-ok: mirrors a hardware bezel */\n",
        encoding="utf-8",
    )
    assert run_logical(fake_frontend).returncode == 0


def test_build_output_is_not_scanned(fake_frontend: Path) -> None:
    """Generated CSS is minified onto one line and rewritten by the bundler, so faults
    found there are neither real nor fixable. This guard read .next once and said so."""
    built = fake_frontend / ".next" / "static"
    built.mkdir(parents=True)
    (built / "chunk.css").write_text(".x{margin-left:4px}\n", encoding="utf-8")
    assert run_logical(fake_frontend).returncode == 0


def test_logical_guard_fails_when_it_cannot_run(tmp_path: Path) -> None:
    assert run_logical(tmp_path / "absent").returncode != 0


# ------------------------------------------------------------- access consulted


def test_access_rejects_a_service_method_that_never_asks(fake_repo: Path) -> None:
    """The mistake it exists to catch: a method that looks complete, returns the right
    type, and hands survey data to whoever called it without ever asking who they are."""
    (fake_repo / "app" / "templates" / "service.py").write_text(
        "from app.templates.models import SurveyTemplate\n\n\n"
        "class S:\n"
        "    async def get(self, tid) -> SurveyTemplate:\n"
        "        return await self.repo.get(tid)\n",
        encoding="utf-8",
    )
    result = run_guard("check_access_consulted.py", fake_repo)
    assert result.returncode == 1
    assert "without consulting app/access" in result.stderr


def test_access_accepts_a_method_that_asks_through_a_private_helper(fake_repo: Path) -> None:
    """How these services are really written: ownership is settled once in a shared
    helper. A guard blind to that would teach people to write exemptions instead."""
    (fake_repo / "app" / "templates" / "service.py").write_text(
        "from app.templates.models import SurveyTemplate\n\n\n"
        "class S:\n"
        "    async def get(self, tid) -> SurveyTemplate:\n"
        "        return await self._owned(tid)\n\n"
        "    async def _owned(self, tid) -> SurveyTemplate:\n"
        "        if not may_list(self.user, None, None, False):\n"
        "            raise NotFoundError()\n"
        "        return await self.repo.get(tid)\n",
        encoding="utf-8",
    )
    assert run_guard("check_access_consulted.py", fake_repo).returncode == 0


def test_access_rejects_an_exemption_with_no_reason(fake_repo: Path) -> None:
    """An exemption is a sentence somebody has to write. A bare marker is how a rule
    quietly stops applying."""
    (fake_repo / "app" / "templates" / "service.py").write_text(
        "from app.templates.models import SurveyTemplate\n\n\n"
        "class S:\n"
        "    async def get(self, tid) -> SurveyTemplate:\n"
        '        """access-exempt:"""\n'
        "        return await self.repo.get(tid)\n",
        encoding="utf-8",
    )
    result = run_guard("check_access_consulted.py", fake_repo)
    assert result.returncode == 1
    assert "no reason given" in result.stderr


def test_access_sees_through_a_wrapped_return_type(fake_repo: Path) -> None:
    """Wrapping the leak in a list does not make it less of a leak."""
    (fake_repo / "app" / "templates" / "service.py").write_text(
        "from app.templates.models import SurveyTemplate\n\n\n"
        "class S:\n"
        "    async def all(self) -> list[tuple[SurveyTemplate, int]]:\n"
        "        return await self.repo.all()\n",
        encoding="utf-8",
    )
    assert run_guard("check_access_consulted.py", fake_repo).returncode == 1


# ------------------------------------------------------------ the eval ratchet


def _corpus(root: Path, *, answers: int, invented: int = 0, traced: bool = True) -> None:
    """A fake tests/live_runs holding one fixture, plus a baseline that matches it."""
    live_runs = root / "tests" / "live_runs"
    live_runs.mkdir(parents=True, exist_ok=True)
    fixture = {
        "scenario": "demo",
        "model": "gpt-4o-mini",
        "status": "completed",
        "respondent_messages": ["line lead"],
        "answers": [
            {"kind": "scripted", "value": {"text": "Line lead"}, "invented": i < invented}
            for i in range(answers)
        ],
    }
    if traced:
        fixture["trace"] = {
            "total": 1,
            "positions": [0],
            "questions": [{"id": "q1", "position": 0, "follow_up_policy": "never"}],
            "answers": [{"question_id": "q1", "kind": "scripted"}],
        }
    (live_runs / "demo.json").write_text(json.dumps(fixture), encoding="utf-8")
    (root / "tests" / "eval_baseline.json").write_text(
        json.dumps({"answers": answers, "known_inventions": invented, "traced_fixtures": 1}),
        encoding="utf-8",
    )


def test_a_corpus_that_matches_its_baseline_passes(tmp_path: Path) -> None:
    _corpus(tmp_path, answers=4, invented=1)
    result = run_guard("eval_report.py", tmp_path)
    assert result.returncode == 0, result.stderr
    assert "ok: eval corpus ratchet" in result.stdout


def test_a_shrinking_corpus_is_rejected(tmp_path: Path) -> None:
    """The regression this exists for. Fixtures are the only record of a live finding, and
    deleting one silently narrows what every future push is checked against."""
    _corpus(tmp_path, answers=4)
    (tmp_path / "tests" / "eval_baseline.json").write_text(
        json.dumps({"answers": 9, "known_inventions": 0, "traced_fixtures": 1}), encoding="utf-8"
    )
    result = run_guard("eval_report.py", tmp_path)
    assert result.returncode == 1
    assert "answers fell from 9 to 4" in result.stderr


def test_unmarking_a_known_invention_is_rejected(tmp_path: Path) -> None:
    """`invented: true` is the one field a human writes, and it is what turns a live
    finding into a permanent test. Quietly clearing one would retire that test with no
    other sign."""
    _corpus(tmp_path, answers=4, invented=0)
    (tmp_path / "tests" / "eval_baseline.json").write_text(
        json.dumps({"answers": 4, "known_inventions": 2, "traced_fixtures": 1}), encoding="utf-8"
    )
    result = run_guard("eval_report.py", tmp_path)
    assert result.returncode == 1
    assert "known_inventions fell from 2 to 0" in result.stderr


def test_a_trace_that_violates_an_invariant_is_rejected(tmp_path: Path) -> None:
    """Not a count but still a fact: a recorded conversation where the engine went
    backwards is a bug, whatever the corpus size says."""
    _corpus(tmp_path, answers=1)
    path = tmp_path / "tests" / "live_runs" / "demo.json"
    fixture = json.loads(path.read_text(encoding="utf-8"))
    fixture["trace"]["positions"] = [1, 0]
    path.write_text(json.dumps(fixture), encoding="utf-8")
    result = run_guard("eval_report.py", tmp_path)
    assert result.returncode == 1
    assert "advances by at most one" in result.stderr


def test_the_ratchet_fails_when_there_is_no_corpus(tmp_path: Path) -> None:
    """The failure mode this whole file is about. An empty corpus checks nothing, and a
    checker that reports success over it is worse than no checker."""
    result = run_guard("eval_report.py", tmp_path)
    assert result.returncode != 0
    assert "cannot run" in result.stderr


def test_the_ratchet_fails_when_the_baseline_is_missing(tmp_path: Path) -> None:
    """A corpus with nothing to measure against cannot regress, which would make this
    guard green forever the moment somebody deleted one file."""
    _corpus(tmp_path, answers=3)
    (tmp_path / "tests" / "eval_baseline.json").unlink()
    result = run_guard("eval_report.py", tmp_path)
    assert result.returncode == 1
    assert "missing" in result.stderr
