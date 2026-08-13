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
    # Sized for the plant's actual traffic shape, which is a burst: the floor answers
    # surveys on breaks, so the load is near zero most of the day and then roughly a
    # shift's worth of people at once for half an hour. A conduct turn checks its
    # connection out when it loads the run and holds it through the LLM call, seconds at
    # a time, so concurrent respondents map one-to-one onto held connections. The
    # SQLAlchemy defaults (5 + 10 overflow) put half of a 30-person break in the pool
    # queue, where the default 30s wait turns into a 500 mid-conversation.
    #
    # 10 + 30 covers that burst with room for the authors watching it happen, and stays
    # comfortably under Postgres's default max_connections of 100.
    db_pool_size: int = Field(10, gt=0, description="Connections kept open in the pool")
    db_pool_max_overflow: int = Field(
        30, ge=0, description="Extra connections allowed above the pool during a burst"
    )
    # The LLM tiers form one ordered failover chain. Tier 1 serves every turn until it
    # raises, then tier 2, and so on; the intended order is OpenAI, Groq, then OpenRouter,
    # with tier 4 left as a spare slot. Every tier speaks the OpenAI Chat Completions API,
    # so any compatible endpoint fits (OpenAI itself, Groq, OpenRouter, vLLM, Ollama).
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

    # Last resort, and an empty slot by default. This held a local Ollama shipped in
    # docker-compose.yml until 8 Aug 2026; nothing is wired here now, so the tier stays
    # off unless someone points it at a server of their own.
    llm_tier4_enabled: bool = Field(False, description="Enable tier 4, the last resort")
    llm_tier4_base_url: str = Field(
        "", description="Tier 4 base URL, e.g. http://localhost:11434/v1"
    )
    llm_tier4_api_key: str = Field("", description="Tier 4 API key (blank if not required)")
    llm_tier4_model: str = Field("", description="Tier 4 model id")
    llm_tier4_timeout_seconds: float = Field(
        120.0, gt=0, description="Read timeout for tier 4, in seconds"
    )

    # What each tier costs and what is serving it, for the spend ledger. Separate from
    # the connection settings above because they answer a different question: those say
    # how to reach a tier, these say what reaching it is worth.
    #
    # params_b is configuration because no provider reports it, and it is the axis the
    # measurement turns on: the same token count means one thing from a 3B model and
    # another from a 70B one. Zero reads as "not stated" in the ledger.
    #
    # A local tier bills no tokens, so its prices stay zero and `local=True` prices it
    # from wall clock against hardware_watts and electricity_price_per_kwh instead.
    # Without that flag a locally served run reports as free, which is the one number
    # that is certainly wrong.
    llm_tier1_params_b: float = Field(0.0, ge=0, description="Tier 1 model size in billions")
    llm_tier1_local: bool = Field(False, description="Tier 1 runs on our own hardware")
    llm_tier1_price_in_per_mtok: float = Field(0.0, ge=0, description="Tier 1 USD/1M input")
    llm_tier1_price_out_per_mtok: float = Field(0.0, ge=0, description="Tier 1 USD/1M output")

    llm_tier2_params_b: float = Field(0.0, ge=0, description="Tier 2 model size in billions")
    llm_tier2_local: bool = Field(False, description="Tier 2 runs on our own hardware")
    llm_tier2_price_in_per_mtok: float = Field(0.0, ge=0, description="Tier 2 USD/1M input")
    llm_tier2_price_out_per_mtok: float = Field(0.0, ge=0, description="Tier 2 USD/1M output")

    llm_tier3_params_b: float = Field(0.0, ge=0, description="Tier 3 model size in billions")
    llm_tier3_local: bool = Field(False, description="Tier 3 runs on our own hardware")
    llm_tier3_price_in_per_mtok: float = Field(0.0, ge=0, description="Tier 3 USD/1M input")
    llm_tier3_price_out_per_mtok: float = Field(0.0, ge=0, description="Tier 3 USD/1M output")

    # Tier 4 now defaults like the rest rather than describing the 3B local model that
    # used to be wired into it. Anyone filling the slot with a model they serve
    # themselves has to say so, which is what the .env.example note beside these is for.
    llm_tier4_params_b: float = Field(0.0, ge=0, description="Tier 4 model size in billions")
    llm_tier4_local: bool = Field(False, description="Tier 4 runs on our own hardware")
    llm_tier4_price_in_per_mtok: float = Field(0.0, ge=0, description="Tier 4 USD/1M input")
    llm_tier4_price_out_per_mtok: float = Field(0.0, ge=0, description="Tier 4 USD/1M output")

    # What the machine draws while it is serving a local tier, and what that energy
    # costs. Defaults are a mid-range desktop under load on a UK domestic tariff; both
    # are guesses until measured, and the ledger records what it was told rather than
    # pretending to know. Fold amortised hardware into the tariff if you want it counted.
    hardware_watts: float = Field(
        200.0, ge=0, description="Power draw while serving a local tier, in watts"
    )
    electricity_price_per_kwh: float = Field(
        0.32, ge=0, description="Electricity price in USD per kWh"
    )
    llm_ledger_path: str = Field(
        "var/llm_ledger.jsonl",
        description="Append-only JSONL record of every model call, for offline analysis",
    )

    # Comma-separated emails that get administrator rights: every survey visible, every
    # response readable. Configuration rather than a column so that granting it is not a
    # database edit and so an admin can still belong to a real department. The cost is
    # that it is easy to change and hard to audit, which is why app.access logs every time
    # this is what let a request through.
    admin_emails: str = Field(
        "", description="Comma-separated admin emails, e.g. you@example.com,ops@example.com"
    )

    @property
    def admin_email_set(self) -> frozenset[str]:
        """The allowlist as a set, case-folded, with blanks and stray spaces dropped."""
        return frozenset(e.strip().casefold() for e in self.admin_emails.split(",") if e.strip())

    # What the interviewer should know about this workplace, for every survey published
    # from this deployment. A survey may still carry its own, and that wins; this is the
    # answer to "the plant does not change between surveys", which is why it is
    # deployment config rather than a box on every draft.
    #
    # It is background for reading answers, never spoken to a respondent and never an
    # instruction: the conduct prompt says so, and treats it as data exactly as it treats
    # a respondent's message. Standards vocabulary belongs here (cold chain, batch codes,
    # HACCP, BRCGS) because it decides whether a reply is specific or vague, and no gate
    # can settle that. It does not make anything compliant with anything; it makes the
    # interviewer able to tell a chill-chain breach from a digression.
    survey_setting: str = Field(
        "",
        description="Background about the workplace for the conducting AI, used by every "
        "survey published here that does not carry its own. Never shown to respondents.",
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
