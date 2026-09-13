"""An enabled hosted tier states its prices, or settings refuse to load.

Every hosted call in the ledger was booked as free until 13 Sep 2026, because zero was
both the price of a free model and the default for a price nobody set. The refusal is
tested by trying to violate it, one way per path in: a missing price, a blank one as
compose forwards it, and the configurations that must still load.
"""

from typing import Any

import pytest
from pydantic import ValidationError

from app.config import Settings

_OPENAI = {
    "llm_tier1_enabled": True,
    "llm_tier1_base_url": "https://api.openai.com/v1",
    "llm_tier1_model": "gpt-test",
}


def _settings(**values: Any) -> Settings:
    # _env_file=None so a developer's own .env cannot answer for the test.
    return Settings(
        _env_file=None, database_url="postgresql+asyncpg://user:pass@localhost/db", **values
    )


def test_an_enabled_hosted_tier_with_no_price_refuses_to_load() -> None:
    with pytest.raises(ValidationError) as caught:
        _settings(**_OPENAI)
    message = str(caught.value)
    assert "LLM_TIER1_PRICE_IN_PER_MTOK and LLM_TIER1_PRICE_OUT_PER_MTOK" in message
    assert "recorded as free" in message


def test_half_a_price_is_still_refused_and_names_the_missing_half() -> None:
    with pytest.raises(ValidationError) as caught:
        _settings(**_OPENAI, llm_tier1_price_in_per_mtok=5.0)
    assert "LLM_TIER1_PRICE_OUT_PER_MTOK" in str(caught.value)
    assert "LLM_TIER1_PRICE_IN_PER_MTOK" not in str(caught.value)


def test_a_blank_price_as_compose_forwards_it_counts_as_unstated() -> None:
    with pytest.raises(ValidationError):
        _settings(**_OPENAI, llm_tier1_price_in_per_mtok="", llm_tier1_price_out_per_mtok="")


def test_zero_is_a_price_and_loads() -> None:
    """A free model is configured, not missing."""
    settings = _settings(**_OPENAI, llm_tier1_price_in_per_mtok=0, llm_tier1_price_out_per_mtok=0)
    assert settings.llm_tier1_price_in_per_mtok == 0.0


def test_a_local_tier_needs_no_price() -> None:
    """It is priced by the clock."""
    _settings(**_OPENAI, llm_tier1_local=True)


def test_a_disabled_tier_needs_no_price() -> None:
    settings = _settings(llm_tier2_enabled=False)
    assert settings.llm_tier2_price_in_per_mtok is None
