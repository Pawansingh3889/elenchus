"""The factory assembles the failover chain from settings, in the right order.

Settings are supplied directly (bypassing the real environment) and the Anthropic client
is stubbed where a key is claimed, so no network or API key is touched.
"""

from typing import Any

import pytest

from app.config import Settings
from app.llm import factory
from app.llm.backup import OpenAICompatibleLLMClient
from app.llm.client import LLMError
from app.llm.failover import FailoverLLM


def _settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {"database_url": "postgresql+asyncpg://user:pass@localhost/db"}
    values.update(overrides)
    return Settings(**values)


_CEREBRAS = {
    "llm_backup_enabled": True,
    "llm_backup_base_url": "https://api.cerebras.ai/v1",
    "llm_backup_model": "llama-3.3-70b",
}
_GROQ = {
    "llm_backup2_enabled": True,
    "llm_backup2_base_url": "https://api.groq.com/openai/v1",
    "llm_backup2_model": "llama-3.3-70b-versatile",
}


def test_two_backups_chain_in_configured_order(monkeypatch):
    monkeypatch.setattr(factory, "get_settings", lambda: _settings(**_CEREBRAS, **_GROQ))

    llm = factory.get_llm()

    assert isinstance(llm, FailoverLLM)
    assert [type(c) for c in llm._clients] == [
        OpenAICompatibleLLMClient,
        OpenAICompatibleLLMClient,
    ]
    assert llm._clients[0]._base_url == "https://api.cerebras.ai/v1"  # Cerebras leads
    assert llm._clients[1]._base_url == "https://api.groq.com/openai/v1"  # Groq second


def test_the_primary_leads_the_chain_when_its_key_is_set(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: _settings(anthropic_api_key="sk-ant-x", **_CEREBRAS, **_GROQ),
    )
    monkeypatch.setattr(factory, "LLMClient", lambda: sentinel)

    llm = factory.get_llm()

    assert isinstance(llm, FailoverLLM)
    assert len(llm._clients) == 3
    assert llm._clients[0] is sentinel  # Anthropic, ahead of both backups


def test_a_single_configured_tier_is_used_bare(monkeypatch):
    monkeypatch.setattr(factory, "get_settings", lambda: _settings(**_CEREBRAS))

    llm = factory.get_llm()

    assert isinstance(llm, OpenAICompatibleLLMClient)


def test_an_enabled_but_unconfigured_tier_fails_loudly(monkeypatch):
    monkeypatch.setattr(factory, "get_settings", lambda: _settings(llm_backup_enabled=True))

    with pytest.raises(LLMError):
        factory.get_llm()
