"""Load versioned prompt files by name.

Prompts are code: they live under ``prompts/`` and are loaded by name + version
(e.g. ``generate_template_v2``), never inlined as string literals in services.
"""

from pathlib import Path

from app.errors import AppError

PROMPTS_DIR = Path(__file__).parent / "prompts"


class PromptNotFoundError(AppError):
    """A prompt the code asks for is not on disk.

    Typed rather than the ``FileNotFoundError`` this used to raise, which is an
    ``OSError``, which the handler in ``app.errors`` renders as "the service cannot
    reach its database". That handler's wide net is deliberate and correct for what it
    is for: asyncpg reports a downed Postgres as a plain OSError. It just meant that
    renaming a prompt told the operator to go and investigate a database that was fine,
    while ``/health`` said "ok" and disagreed with every other endpoint.

    500, not 503: this is a build that shipped without one of its own files. Retrying
    changes nothing, and no amount of waiting brings the prompt back.
    """

    status_code = 500
    code = "prompt_not_found"


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise PromptNotFoundError(f"Prompt not found: {name}")
    return path.read_text(encoding="utf-8").strip()
