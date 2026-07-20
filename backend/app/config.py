"""Application settings, loaded from the environment.

Required settings have no default, so a missing value fails loudly at startup
rather than silently degrading (see ARCHITECTURE.md — no fallbacks).
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(
        ..., description="Async SQLAlchemy URL, e.g. postgresql+asyncpg://user:pass@host/db"
    )
    # Only needed for LLM features; the LLM client validates its presence at use,
    # so the scaffold and CRUD run without it.
    anthropic_api_key: str = Field("", description="Anthropic API key")
    anthropic_model: str = Field("claude-sonnet-5", description="Anthropic model id")

    app_env: str = Field("dev", description="dev | prod")


@lru_cache
def get_settings() -> Settings:
    return Settings()
