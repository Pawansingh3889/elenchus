"""Every LLM setting the code reads is forwarded to the container that runs it.

Compose reads the root ``.env`` only to interpolate ``${...}`` inside its own file, so
a service sees exactly the variables its ``environment:`` block names and nothing else.
That makes the block a hand-maintained copy of part of ``Settings``, and the copy fell
behind the moment the spend ledger added pricing fields: an operator set the prices
documented in ``.env.example``, compose never passed them on, and every hosted call was
recorded at zero cost with no way to reprice it afterwards.

Asserted rather than remembered, because the failure is silent at every layer. The
container starts, the tiers answer, the ledger fills up, and only the numbers are wrong.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml

from app.config import Settings

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILES = ("docker-compose.yml", "docker-compose.prod.yml")

# Everything the LLM stack reads, by prefix, plus the two that price a local tier from
# the clock and so carry no llm_ prefix of their own.
FORWARDED_PREFIXES = ("llm_",)
FORWARDED_EXTRAS = ("hardware_watts", "electricity_price_per_kwh")


def _must_be_forwarded() -> set[str]:
    fields = {
        name
        for name in Settings.model_fields
        if name.startswith(FORWARDED_PREFIXES) or name in FORWARDED_EXTRAS
    }
    assert fields, "no LLM settings found; this test is checking nothing"
    return {name.upper() for name in fields}


def _backend_environment(compose_file: str) -> dict[str, Any]:
    path = REPO_ROOT / compose_file
    assert path.exists(), f"{compose_file} is missing; this test cannot run"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    environment = document["services"]["backend"]["environment"]
    assert isinstance(environment, dict), f"{compose_file} uses list-form environment"
    return environment


@pytest.mark.parametrize("compose_file", COMPOSE_FILES)
def test_every_llm_setting_reaches_the_backend_container(compose_file: str) -> None:
    missing = sorted(_must_be_forwarded() - set(_backend_environment(compose_file)))
    assert not missing, (
        f"{compose_file} does not forward {missing} to the backend, so the container "
        f"falls back to the code defaults for them however the operator sets .env"
    )


@pytest.mark.parametrize("compose_file", COMPOSE_FILES)
def test_the_local_tier_is_marked_local_so_it_is_not_priced_at_zero(
    compose_file: str,
) -> None:
    """Tier 4 bills no tokens, so without this flag it reports as free rather than
    being priced from wall clock, which is the one number that is certainly wrong."""
    environment = _backend_environment(compose_file)
    assert "true" in str(environment["LLM_TIER4_LOCAL"]).lower()
