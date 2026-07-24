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

    # Backup LLMs form an ordered failover chain after the Anthropic primary: the first
    # backup is tried when the primary fails, the second when the first also fails. Each is
    # any OpenAI-compatible endpoint (Cerebras, Groq, OpenRouter, a self-hosted server…).
    # If the primary key is absent the first configured backup leads. base_url/model are
    # required when a tier is enabled; api_key may be blank for keyless local servers.
    llm_backup_enabled: bool = Field(False, description="Enable the first backup LLM")
    llm_backup_base_url: str = Field(
        "", description="First backup base URL, e.g. https://api.cerebras.ai/v1"
    )
    llm_backup_api_key: str = Field("", description="First backup API key (blank if not required)")
    llm_backup_model: str = Field("", description="First backup model id, e.g. llama-3.3-70b")
    # Local CPU-served models can take >60s on a cold load; a genuinely unreachable
    # endpoint still fails fast via the separate connect timeout.
    llm_backup_timeout_seconds: float = Field(
        120.0, gt=0, description="Read timeout for the first backup, in seconds"
    )

    # Second backup, tried only when both the primary and the first backup fail.
    llm_backup2_enabled: bool = Field(False, description="Enable the second backup LLM")
    llm_backup2_base_url: str = Field(
        "", description="Second backup base URL, e.g. https://api.groq.com/openai/v1"
    )
    llm_backup2_api_key: str = Field(
        "", description="Second backup API key (blank if not required)"
    )
    llm_backup2_model: str = Field(
        "", description="Second backup model id, e.g. llama-3.3-70b-versatile"
    )
    llm_backup2_timeout_seconds: float = Field(
        120.0, gt=0, description="Read timeout for the second backup, in seconds"
    )

    app_env: str = Field("dev", description="dev | prod")
    frontend_origin: str = Field(
        "http://localhost:3000", description="Allowed CORS origin for the browser app"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
