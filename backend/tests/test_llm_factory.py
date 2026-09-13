"""The factory assembles the failover chain from settings, in the right order.

Settings are supplied directly, bypassing the real environment, and no client ever
sends a request, so no network or API key is touched.
"""

from typing import Any

import pytest

from app.config import Settings
from app.llm import factory
from app.llm.client import LLMError
from app.llm.failover import FailoverLLM
from app.llm.openai_compatible import OpenAICompatibleLLMClient


def _settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {"database_url": "postgresql+asyncpg://user:pass@localhost/db"}
    values.update(overrides)
    # _env_file=None is what makes the docstring above true. Keyword arguments override
    # only the keys they name, so without this Settings still reads backend/.env and any
    # LLM_TIER* the developer keeps there leaks into a test that means to describe a
    # machine with no tiers at all. Three tests here inverted on 27 Aug 2026 the moment a
    # real tier 1 key was put in that file for local work: "no configured tier fails
    # loudly" found a configured tier and did not raise. CI never saw it, because CI has
    # no .env, which is the worst shape for a failure to have.
    return Settings(_env_file=None, **values)


_OPENAI = {
    "llm_tier1_enabled": True,
    "llm_tier1_base_url": "https://api.openai.com/v1",
    "llm_tier1_model": "gpt-test",
    # Every enabled hosted tier states its prices or settings refuse to load.
    "llm_tier1_price_in_per_mtok": 5.0,
    "llm_tier1_price_out_per_mtok": 30.0,
}
_GROQ = {
    "llm_tier2_enabled": True,
    "llm_tier2_base_url": "https://api.groq.com/openai/v1",
    "llm_tier2_model": "llama-3.3-70b-versatile",
    "llm_tier2_price_in_per_mtok": 0.59,
    "llm_tier2_price_out_per_mtok": 0.79,
}
_OPENROUTER = {
    "llm_tier3_enabled": True,
    "llm_tier3_base_url": "https://openrouter.ai/api/v1",
    "llm_tier3_model": "openrouter/free",
    "llm_tier3_price_in_per_mtok": 0,
    "llm_tier3_price_out_per_mtok": 0,
}
# Tier 4 is a spare slot with nothing shipped in it, so this stands for whatever an
# operator points at: a self-hosted server here, but the chain does not care which.
_TIER4 = {
    "llm_tier4_enabled": True,
    "llm_tier4_base_url": "http://localhost:11434/v1",
    "llm_tier4_model": "a-local-model",
    # Local, so priced by the clock rather than per token. Stated here rather than left
    # to conftest's environment, so this dict means the same thing wherever it is used.
    "llm_tier4_local": True,
}


def test_two_tiers_chain_in_configured_order(monkeypatch):
    monkeypatch.setattr(factory, "get_settings", lambda: _settings(**_OPENAI, **_GROQ))

    llm = factory.get_llm()

    assert isinstance(llm, FailoverLLM)
    assert [type(c) for c in llm._clients] == [
        OpenAICompatibleLLMClient,
        OpenAICompatibleLLMClient,
    ]
    assert llm._clients[0]._base_url == "https://api.openai.com/v1"  # OpenAI leads
    assert llm._clients[1]._base_url == "https://api.groq.com/openai/v1"  # Groq second


def test_the_whole_chain_runs_all_four_tiers_in_order(monkeypatch):
    """The configured order, and the one the failover wrapper walks."""
    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: _settings(**_OPENAI, **_GROQ, **_OPENROUTER, **_TIER4),
    )

    llm = factory.get_llm()

    assert isinstance(llm, FailoverLLM)
    assert [c._base_url for c in llm._clients] == [
        "https://api.openai.com/v1",
        "https://api.groq.com/openai/v1",
        "https://openrouter.ai/api/v1",
        "http://localhost:11434/v1",  # last resort
    ]


def test_a_gap_in_the_middle_does_not_reorder_the_rest(monkeypatch):
    """Tier order is positional. Disabling tier 2 promotes nothing: 1, 3 and 4 keep
    their relative order rather than sliding into the free slot."""
    monkeypatch.setattr(
        factory, "get_settings", lambda: _settings(**_OPENAI, **_OPENROUTER, **_TIER4)
    )

    llm = factory.get_llm()

    assert [c._base_url for c in llm._clients] == [
        "https://api.openai.com/v1",
        "https://openrouter.ai/api/v1",
        "http://localhost:11434/v1",
    ]


def test_a_single_configured_tier_is_used_bare(monkeypatch):
    monkeypatch.setattr(factory, "get_settings", lambda: _settings(**_GROQ))

    llm = factory.get_llm()

    assert isinstance(llm, OpenAICompatibleLLMClient)


def test_no_configured_tier_fails_loudly(monkeypatch):
    """The one case with nothing to fall back to. It must raise rather than hand back
    something that fails later, further from the cause."""
    monkeypatch.setattr(factory, "get_settings", lambda: _settings())

    with pytest.raises(LLMError, match="No LLM tier is configured"):
        factory.get_llm()


def test_an_enabled_but_unconfigured_tier_fails_loudly(monkeypatch):
    # Priced, so the refusal under test is the factory's missing base URL and model
    # rather than the settings' missing price.
    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: _settings(
            llm_tier1_enabled=True, llm_tier1_price_in_per_mtok=0, llm_tier1_price_out_per_mtok=0
        ),
    )

    with pytest.raises(LLMError):
        factory.get_llm()


def test_embeddings_that_are_not_configured_are_a_loud_503(monkeypatch):
    from app.llm.client import EmbeddingsNotConfiguredError

    monkeypatch.setattr(factory, "get_settings", lambda: _settings())
    with pytest.raises(EmbeddingsNotConfiguredError) as caught:
        factory.get_embedder()
    assert caught.value.status_code == 503


def test_configured_embeddings_build_a_priced_client(monkeypatch):
    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: _settings(
            llm_embedding_enabled=True,
            llm_embedding_base_url="https://api.openai.com/v1",
            llm_embedding_price_per_mtok=0.02,
        ),
    )
    embedder = factory.get_embedder()
    assert embedder.model == "text-embedding-3-small"


def test_a_pinned_tier_is_that_tier_alone_and_one_that_is_off_is_refused(monkeypatch) -> None:
    """An evaluation pinned to a model must fail when that model does, never fall through."""
    monkeypatch.setattr(factory, "_merged_settings", lambda: _settings(**_OPENAI, **_GROQ))

    client = factory.get_llm_for_tier(2)

    assert isinstance(client, OpenAICompatibleLLMClient)
    assert client.model == "llama-3.3-70b-versatile"
    assert factory.enabled_tiers() == [(1, "gpt-test"), (2, "llama-3.3-70b-versatile")]
    with pytest.raises(LLMError, match="Tier 3 is not enabled"):
        factory.get_llm_for_tier(3)
    with pytest.raises(LLMError, match="There is no tier 5"):
        factory.get_llm_for_tier(5)
