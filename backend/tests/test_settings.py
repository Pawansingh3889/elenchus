"""Runtime settings service and LLM factory integration."""

import pytest
from app.settings.schemas import SettingsUpdate, TierConfig
from app.settings.service import SettingsService

from app.config import Settings
from app.llm import factory
from app.llm.openai_compatible import OpenAICompatibleLLMClient


def _settings(**overrides):
    values: dict = {"database_url": "postgresql+asyncpg://user:pass@localhost/db"}
    values.update(overrides)
    return Settings(**values)


@pytest.mark.asyncio
async def test_read_empty_settings_returns_empty_config(session):
    service = SettingsService(session)
    result = await service.read()
    assert result.tier_config == {}


@pytest.mark.asyncio
async def test_update_settings_persists_and_returns_config(session):
    service = SettingsService(session)
    data = SettingsUpdate(
        tier_config={
            "1": TierConfig(
                enabled=True,
                timeout_seconds=60.0,
                prompt_cache=True,
                max_completion_tokens=2048,
            ),
        }
    )
    result = await service.update(data)
    assert result.tier_config["1"].enabled is True
    assert result.tier_config["1"].timeout_seconds == 60.0
    assert result.tier_config["1"].prompt_cache is True
    assert result.tier_config["1"].max_completion_tokens == 2048


@pytest.mark.asyncio
async def test_update_settings_partial_merge(session):
    service = SettingsService(session)
    await service.update(
        SettingsUpdate(
            tier_config={
                "1": TierConfig(enabled=True, timeout_seconds=60.0),
            }
        )
    )
    result = await service.update(
        SettingsUpdate(
            tier_config={
                "1": TierConfig(prompt_cache=True),
            }
        )
    )
    assert result.tier_config["1"].enabled is True
    assert result.tier_config["1"].timeout_seconds == 60.0
    assert result.tier_config["1"].prompt_cache is True


def test_factory_uses_runtime_override_for_max_tokens(monkeypatch):
    monkeypatch.setattr(
        factory,
        "_runtime_overrides",
        {
            "1": {"max_completion_tokens": 2048},
        },
    )
    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: _settings(
            llm_tier1_enabled=True,
            llm_tier1_base_url="https://api.openai.com/v1",
            llm_tier1_model="gpt-test",
        ),
    )
    llm = factory.get_llm()
    assert isinstance(llm, OpenAICompatibleLLMClient)
    assert llm._max_completion_tokens == 2048


def test_factory_falls_back_to_env_when_no_override(monkeypatch):
    monkeypatch.setattr(factory, "_runtime_overrides", {})
    monkeypatch.setattr(
        factory,
        "get_settings",
        lambda: _settings(
            llm_tier1_enabled=True,
            llm_tier1_base_url="https://api.openai.com/v1",
            llm_tier1_model="gpt-test",
        ),
    )
    llm = factory.get_llm()
    assert isinstance(llm, OpenAICompatibleLLMClient)
    assert llm._max_completion_tokens == 4096


def test_apply_runtime_overrides_updates_factory_cache():
    factory.apply_runtime_overrides({"1": {"max_completion_tokens": 1024}})
    assert factory._runtime_overrides["1"]["max_completion_tokens"] == 1024
    factory.apply_runtime_overrides({})
