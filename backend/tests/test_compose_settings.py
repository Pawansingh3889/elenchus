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


def _compose_default(value: Any) -> str:
    """The default out of a ``${NAME:-default}`` interpolation, or the literal value."""
    text = str(value).strip()
    if text.startswith("${") and ":-" in text:
        return text[: -1 if text.endswith("}") else None].split(":-", 1)[1]
    return text


def _local_tiers_priced_at_nothing(environment: dict[str, Any]) -> list[str]:
    """Tiers this environment defaults to local while giving the clock nothing to bill.

    A local tier bills no tokens, so its cost comes from wall clock against
    ``HARDWARE_WATTS`` and ``ELECTRICITY_PRICE_PER_KWH``. Marked local with either of
    those at zero, every locally served call records as free, which is the one number
    that is certainly wrong.
    """
    local = [
        name
        for name, value in environment.items()
        if name.endswith("_LOCAL") and _compose_default(value).lower() == "true"
    ]
    if not local:
        return []
    clock = ("HARDWARE_WATTS", "ELECTRICITY_PRICE_PER_KWH")
    if all(float(_compose_default(environment.get(name, 0)) or 0) > 0 for name in clock):
        return []
    return local


@pytest.mark.parametrize("compose_file", COMPOSE_FILES)
def test_no_shipped_local_tier_is_priced_at_nothing(compose_file: str) -> None:
    """The inverse of what this asserted while the stack ran its own Ollama.

    Then, tier 4 was local and the risk was forgetting to say so. Now the stack serves
    nothing locally, so the risk runs the other way: someone adds an inference service
    back and the pricing question goes unasked.
    """
    offenders = _local_tiers_priced_at_nothing(_backend_environment(compose_file))
    assert not offenders, (
        f"{compose_file} defaults {offenders} to local without the wall-clock inputs to "
        f"price them, so every locally served call is recorded as free"
    )


def test_that_check_rejects_a_local_tier_with_no_clock_to_bill() -> None:
    """Both compose files currently ship no local tier, so the test above passes without
    reaching its condition. Planted here instead, because a check nobody has watched
    reject anything is decoration."""
    assert _local_tiers_priced_at_nothing(
        {
            "LLM_TIER4_LOCAL": "${LLM_TIER4_LOCAL:-true}",
            "HARDWARE_WATTS": "${HARDWARE_WATTS:-0}",
            "ELECTRICITY_PRICE_PER_KWH": "${ELECTRICITY_PRICE_PER_KWH:-0.32}",
        }
    ) == ["LLM_TIER4_LOCAL"]
    # And passes the configuration the Ollama tier actually shipped with.
    assert not _local_tiers_priced_at_nothing(
        {
            "LLM_TIER4_LOCAL": "${LLM_TIER4_LOCAL:-true}",
            "HARDWARE_WATTS": "${HARDWARE_WATTS:-200}",
            "ELECTRICITY_PRICE_PER_KWH": "${ELECTRICITY_PRICE_PER_KWH:-0.32}",
        }
    )
