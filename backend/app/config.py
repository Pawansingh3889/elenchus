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

    # Optional backup LLM (any OpenAI-compatible endpoint, e.g. a self-hosted Nemotron/
    # Hermes server). When enabled it is used only if the Anthropic primary fails; if the
    # primary key is absent it is used on its own. base_url/model are required when enabled.
    llm_backup_enabled: bool = Field(False, description="Enable the OpenAI-compatible backup LLM")
    llm_backup_base_url: str = Field(
        "", description="Backup LLM base URL, e.g. http://localhost:8080/v1"
    )
    llm_backup_api_key: str = Field("", description="Backup LLM API key (blank if not required)")
    llm_backup_model: str = Field("", description="Backup LLM model id, e.g. nemotron-3-super-120b")
    # Local CPU-served models can take >60s on a cold load; a genuinely unreachable
    # endpoint still fails fast via the separate connect timeout.
    llm_backup_timeout_seconds: float = Field(
        120.0, gt=0, description="Read timeout for backup LLM calls, in seconds"
    )

    app_env: str = Field("dev", description="dev | prod")
    frontend_origin: str = Field(
        "http://localhost:3000", description="Allowed CORS origin for the browser app"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
