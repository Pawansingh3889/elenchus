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
    # The LLM tiers form one ordered failover chain. Tier 1 serves every turn until it
    # raises, then tier 2, and so on; the intended order is OpenAI, Groq, OpenRouter,
    # then a local Ollama. Every tier speaks the OpenAI Chat Completions API, so any
    # compatible endpoint fits (OpenAI itself, Groq, OpenRouter, vLLM, Ollama).
    #
    # Only the LLM features need these; templates, publishing and results run with no
    # tier configured at all. base_url and model are required once a tier is enabled and
    # the client refuses to construct without them, rather than degrading quietly.
    # api_key stays optional because a local server does not ask for one.
    llm_tier1_enabled: bool = Field(False, description="Enable tier 1, the first tier tried")
    llm_tier1_base_url: str = Field(
        "", description="Tier 1 base URL, e.g. https://api.openai.com/v1"
    )
    llm_tier1_api_key: str = Field("", description="Tier 1 API key (blank if not required)")
    llm_tier1_model: str = Field("", description="Tier 1 model id")
    # Local CPU-served models can take >60s on a cold load; a genuinely unreachable
    # endpoint still fails fast via the separate connect timeout.
    llm_tier1_timeout_seconds: float = Field(
        120.0, gt=0, description="Read timeout for tier 1, in seconds"
    )

    llm_tier2_enabled: bool = Field(False, description="Enable tier 2, tried when tier 1 fails")
    llm_tier2_base_url: str = Field(
        "", description="Tier 2 base URL, e.g. https://api.groq.com/openai/v1"
    )
    llm_tier2_api_key: str = Field("", description="Tier 2 API key (blank if not required)")
    llm_tier2_model: str = Field("", description="Tier 2 model id, e.g. llama-3.3-70b-versatile")
    llm_tier2_timeout_seconds: float = Field(
        120.0, gt=0, description="Read timeout for tier 2, in seconds"
    )

    llm_tier3_enabled: bool = Field(False, description="Enable tier 3, tried when 1 and 2 fail")
    llm_tier3_base_url: str = Field(
        "", description="Tier 3 base URL, e.g. https://openrouter.ai/api/v1"
    )
    llm_tier3_api_key: str = Field("", description="Tier 3 API key (blank if not required)")
    llm_tier3_model: str = Field("", description="Tier 3 model id, e.g. openrouter/free")
    llm_tier3_timeout_seconds: float = Field(
        120.0, gt=0, description="Read timeout for tier 3, in seconds"
    )

    # Last resort, and the one that runs with no credit attached: a local Ollama.
    llm_tier4_enabled: bool = Field(False, description="Enable tier 4, the last resort")
    llm_tier4_base_url: str = Field(
        "", description="Tier 4 base URL, e.g. http://localhost:11434/v1"
    )
    llm_tier4_api_key: str = Field("", description="Tier 4 API key (blank if not required)")
    llm_tier4_model: str = Field("", description="Tier 4 model id, e.g. llama3.2:3b")
    llm_tier4_timeout_seconds: float = Field(
        120.0, gt=0, description="Read timeout for tier 4, in seconds"
    )

    app_env: str = Field("dev", description="dev | prod")
    frontend_origin: str = Field(
        "http://localhost:3000", description="Allowed CORS origin for the browser app"
    )
    log_level: str = Field(
        "INFO",
        description="Level for the app.* loggers. INFO keeps the per-call token-usage "
        "records ARCHITECTURE.md requires; raise to WARNING to quieten them.",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
