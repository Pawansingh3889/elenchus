"""Application settings, loaded from the environment.

Required settings have no default, so a missing value fails loudly at startup
rather than silently degrading (see ARCHITECTURE.md — no fallbacks).
"""

from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PRICE_FIELDS = tuple(
    f"llm_tier{tier}_price_{side}_per_mtok" for tier in range(1, 5) for side in ("in", "out")
)
CACHED_PRICE_FIELDS = tuple(f"llm_tier{tier}_price_cached_in_per_mtok" for tier in range(1, 5))
CONTEXT_WINDOW_FIELDS = tuple(f"llm_tier{tier}_context_window" for tier in range(1, 5))


# The interp service refuses a shorter token; the backend refuses to start with one.
INTERP_TOKEN_MIN_LENGTH = 16


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
    # Opt-in prefix caching (Anthropic/OpenRouter-style `cache_control`). Off by default
    # because OpenAI's API rejects the annotation with a 400, which would drop tier 1 from
    # the chain; enable per tier only for a provider that honours it.
    llm_tier1_prompt_cache: bool = Field(
        True, description="Mark the system prefix cacheable on a caching-capable provider"
    )
    llm_tier1_max_completion_tokens: int = Field(
        4096, gt=0, description="Default max completion tokens for tier 1 tool calls"
    )
    # Unstated by default, like the prices below: no provider reports its own window, and
    # guessing one would be exactly the silent wrong number ARCHITECTURE.md's "no
    # fallbacks" rule exists to rule out. Set, it lets openai_compatible refuse a prompt
    # that would not fit before sending it, rather than learning that from the provider's
    # 400. A tier states its own; nothing here is shared across tiers, because context
    # size is a property of the model behind it, not of the chain.
    llm_tier1_context_window: int | None = Field(
        None, gt=0, description="Tier 1 total context tokens; unset skips the pre-flight check"
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
    llm_tier2_prompt_cache: bool = Field(
        False, description="Mark the system prefix cacheable on a caching-capable provider"
    )
    llm_tier2_max_completion_tokens: int = Field(
        4096, gt=0, description="Default max completion tokens for tier 2 tool calls"
    )
    llm_tier2_context_window: int | None = Field(
        None, gt=0, description="Tier 2 total context tokens; unset skips the pre-flight check"
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
    llm_tier3_prompt_cache: bool = Field(
        False, description="Mark the system prefix cacheable on a caching-capable provider"
    )
    llm_tier3_max_completion_tokens: int = Field(
        1024, gt=0, description="Default max completion tokens for tier 3 tool calls"
    )
    llm_tier3_context_window: int | None = Field(
        None, gt=0, description="Tier 3 total context tokens; unset skips the pre-flight check"
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
    llm_tier4_prompt_cache: bool = Field(
        False, description="Mark the system prefix cacheable on a caching-capable provider"
    )
    llm_tier4_max_completion_tokens: int = Field(
        1024, gt=0, description="Default max completion tokens for tier 4 tool calls"
    )
    # The tier most worth setting this for: whatever fills the empty slot is likeliest to
    # be a small local model, and a survey with several long_text answers is exactly the
    # shape that can walk past a small window without TRANSCRIPT_WINDOW's message count
    # noticing anything wrong.
    llm_tier4_context_window: int | None = Field(
        None, gt=0, description="Tier 4 total context tokens; unset skips the pre-flight check"
    )

    # What each tier costs and what is serving it, for the spend ledger. Separate from
    # the connection settings above because they answer a different question: those say
    # how to reach a tier, these say what reaching it is worth.
    #
    # params_b is configuration because no provider reports it, and it is the axis the
    # measurement turns on: the same token count means one thing from a 3B model and
    # another from a 70B one. Zero reads as "not stated" in the ledger.
    #
    # A local tier bills no tokens, so it needs no prices and `local=True` prices it
    # from wall clock against hardware_watts and electricity_price_per_kwh instead.
    # Without that flag a locally served run reports as free, which is the one number
    # that is certainly wrong.
    #
    # Prices have no default, because zero is a real price (a free model) and it was also
    # what an unstated one looked like. Until 13 Sep 2026 no deployment set them, and
    # 1,808 hosted calls went into the ledger as free with nothing to say so but a
    # warning per process. An enabled hosted tier now has to state both, 0 included, or
    # settings refuse to load.
    llm_tier1_params_b: float = Field(0.0, ge=0, description="Tier 1 model size in billions")
    llm_tier1_local: bool = Field(False, description="Tier 1 runs on our own hardware")
    llm_tier1_price_in_per_mtok: float | None = Field(
        None, ge=0, description="Tier 1 USD/1M input; required when enabled and hosted"
    )
    llm_tier1_price_out_per_mtok: float | None = Field(
        None, ge=0, description="Tier 1 USD/1M output; required when enabled and hosted"
    )
    # Cached input, for a provider that discounts a repeated prefix (gpt-5.5 charges a
    # tenth). Optional, unlike the two above: unset, cached tokens pay the full input
    # rate, which overstates a turn's cost rather than hiding any of it.
    llm_tier1_price_cached_in_per_mtok: float | None = Field(
        None, ge=0, description="Tier 1 USD/1M cached input; unset means the input price"
    )

    llm_tier2_params_b: float = Field(0.0, ge=0, description="Tier 2 model size in billions")
    llm_tier2_local: bool = Field(False, description="Tier 2 runs on our own hardware")
    llm_tier2_price_in_per_mtok: float | None = Field(
        None, ge=0, description="Tier 2 USD/1M input; required when enabled and hosted"
    )
    llm_tier2_price_out_per_mtok: float | None = Field(
        None, ge=0, description="Tier 2 USD/1M output; required when enabled and hosted"
    )
    llm_tier2_price_cached_in_per_mtok: float | None = Field(
        None, ge=0, description="Tier 2 USD/1M cached input; unset means the input price"
    )

    llm_tier3_params_b: float = Field(0.0, ge=0, description="Tier 3 model size in billions")
    llm_tier3_local: bool = Field(False, description="Tier 3 runs on our own hardware")
    llm_tier3_price_in_per_mtok: float | None = Field(
        None, ge=0, description="Tier 3 USD/1M input; required when enabled and hosted"
    )
    llm_tier3_price_out_per_mtok: float | None = Field(
        None, ge=0, description="Tier 3 USD/1M output; required when enabled and hosted"
    )
    llm_tier3_price_cached_in_per_mtok: float | None = Field(
        None, ge=0, description="Tier 3 USD/1M cached input; unset means the input price"
    )

    # Tier 4 now defaults like the rest rather than describing the 3B local model that
    # used to be wired into it. Anyone filling the slot with a model they serve
    # themselves has to say so, which is what the .env.example note beside these is for.
    llm_tier4_params_b: float = Field(0.0, ge=0, description="Tier 4 model size in billions")
    llm_tier4_local: bool = Field(False, description="Tier 4 runs on our own hardware")
    llm_tier4_price_in_per_mtok: float | None = Field(
        None, ge=0, description="Tier 4 USD/1M input; required when enabled and hosted"
    )
    llm_tier4_price_out_per_mtok: float | None = Field(
        None, ge=0, description="Tier 4 USD/1M output; required when enabled and hosted"
    )
    llm_tier4_price_cached_in_per_mtok: float | None = Field(
        None, ge=0, description="Tier 4 USD/1M cached input; unset means the input price"
    )

    # What the machine draws while it is serving a local tier, and what that energy
    # costs. Defaults are a mid-range desktop under load on a UK domestic tariff; both
    # are guesses until measured, and the ledger records what it was told rather than
    # pretending to know. Fold amortised hardware into the tariff if you want it counted.
    @field_validator(
        *PRICE_FIELDS,
        *CACHED_PRICE_FIELDS,
        *CONTEXT_WINDOW_FIELDS,
        "llm_embedding_price_per_mtok",
        "grounding_similarity_margin",
        mode="before",
    )
    @classmethod
    def _a_blank_optional_number_is_unstated(cls, value: object) -> object:
        """Compose forwards a variable nobody set as an empty string, not as an absent
        key, so pydantic sees `''` where an unset optional number needs `None` — and
        for a price, that has to stay distinguishable from 0, the price of a free
        model. Every `int | None` / `float | None` setting fed from a
        `${VAR:-}`-style compose default needs this, not just the price fields the
        name used to promise."""
        return None if value == "" else value

    @model_validator(mode="after")
    def _hosted_tiers_state_their_prices(self) -> "Settings":
        """Refuse to load when an enabled hosted tier has no price.

        Loudly, at startup, rather than per call: the calls themselves succeed, the
        survey works, and the only thing wrong is every cost figure, which is the kind of
        failure nobody notices until the numbers are needed.
        """
        for tier in range(1, 5):
            prefix = f"llm_tier{tier}"
            if not getattr(self, f"{prefix}_enabled") or getattr(self, f"{prefix}_local"):
                continue
            missing = [
                f"LLM_TIER{tier}_PRICE_{side.upper()}_PER_MTOK"
                for side in ("in", "out")
                if getattr(self, f"{prefix}_price_{side}_per_mtok") is None
            ]
            if missing:
                raise ValueError(
                    f"LLM tier {tier} is enabled and hosted, but {' and '.join(missing)} "
                    f"{'is' if len(missing) == 1 else 'are'} not set, so every call it serves "
                    "would be recorded as free. Set the "
                    "provider's USD price per million tokens, or 0 for a genuinely free model."
                )
        return self

    @model_validator(mode="after")
    def _embeddings_are_configured_before_use(self) -> "Settings":
        """Refuse embeddings switched on half-configured, and semantic grounding without them."""
        if self.llm_embedding_enabled:
            missing = [
                name
                for name, value in (
                    ("LLM_EMBEDDING_BASE_URL", self.llm_embedding_base_url),
                    ("LLM_EMBEDDING_MODEL", self.llm_embedding_model),
                )
                if not value
            ]
            if self.llm_embedding_price_per_mtok is None:
                missing.append("LLM_EMBEDDING_PRICE_PER_MTOK")
            if missing:
                raise ValueError(
                    f"Embeddings are enabled but {', '.join(missing)} "
                    f"{'is' if len(missing) == 1 else 'are'} not set."
                )
        if self.grounding_semantic_enabled:
            if not self.llm_embedding_enabled:
                raise ValueError(
                    "GROUNDING_SEMANTIC_ENABLED needs embeddings: set LLM_EMBEDDING_ENABLED "
                    "and its URL, model and price."
                )
            if self.grounding_similarity_margin is None:
                raise ValueError(
                    "GROUNDING_SEMANTIC_ENABLED needs GROUNDING_SIMILARITY_MARGIN, measured "
                    "with backend/scripts/measure_semantic_grounding.py, not guessed."
                )
        return self

    @model_validator(mode="after")
    def _interp_is_configured_before_use(self) -> "Settings":
        """Refuse the interpretability service switched on without an address or a token."""
        if not self.interp_enabled:
            return self
        missing = [
            name
            for name, value in (
                ("INTERP_BASE_URL", self.interp_base_url),
                ("INTERP_TOKEN", self.interp_token),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"INTERP_ENABLED is set but {' and '.join(missing)} not.")
        if len(self.interp_token) < INTERP_TOKEN_MIN_LENGTH:
            raise ValueError(
                f"INTERP_TOKEN must be at least {INTERP_TOKEN_MIN_LENGTH} characters, the same "
                "value the service is started with. Generate one with: openssl rand -hex 24"
            )
        return self

    hardware_watts: float = Field(
        200.0, ge=0, description="Power draw while serving a local tier, in watts"
    )
    electricity_price_per_kwh: float = Field(
        0.32, ge=0, description="Electricity price in USD per kWh"
    )
    # Embeddings, for meaning where words fail: the answer map, themes across free text,
    # and (when switched on below) a second chance for a choice the word check cannot
    # ground. A separate endpoint from the chat tiers, because not every chat provider
    # serves embeddings, and a price that is required once enabled, for the same reason
    # tier prices are.
    llm_embedding_enabled: bool = Field(False, description="Enable the embeddings endpoint")
    llm_embedding_base_url: str = Field(
        "", description="Embeddings base URL, e.g. https://api.openai.com/v1"
    )
    llm_embedding_api_key: str = Field("", description="Embeddings API key")
    llm_embedding_model: str = Field("text-embedding-3-small", description="Embedding model id")
    llm_embedding_timeout_seconds: float = Field(
        30.0, gt=0, description="Read timeout for an embeddings call, in seconds"
    )
    llm_embedding_price_per_mtok: float | None = Field(
        None, ge=0, description="Embeddings USD/1M input tokens; required when enabled"
    )
    # Semantic grounding: let a chosen option the word check rejects count as supported when
    # it is the closest of its question's options to what the respondent said, by at least
    # this margin over the runner-up. Off by default, and the margin has no default at all:
    # it is measured on the labelled set in backend/tests/fixtures/grounding_pairs.json, and
    # a guessed number here would be the gate that records answers nobody gave. Relative,
    # not absolute: one absolute similarity threshold was measured and was too fragile.
    grounding_semantic_enabled: bool = Field(
        False, description="Accept a word-ungrounded choice when its meaning matches"
    )
    grounding_similarity_margin: float | None = Field(
        None,
        ge=0,
        lt=1,
        description="How far above the runner-up option a choice must be to count as supported",
    )
    # The interpretability service (interp/): Qwen3-0.6B reading captured conduct prompts
    # for the lens pages. Off by default, and conduct never uses it: it only reads prompts
    # after the fact, on an administrator's request. It runs on the host, not in the stack,
    # so a Mac can use its GPU; the token is what keeps a listening model private.
    interp_enabled: bool = Field(False, description="Enable the interpretability service")
    interp_base_url: str = Field(
        "", description="Where the service listens, e.g. http://host.docker.internal:8765"
    )
    interp_token: str = Field("", description="The shared token the service requires")
    interp_timeout_seconds: float = Field(
        900, gt=0, description="How long one analysis may take; a CPU reads slowly"
    )
    interp_params_b: float = Field(
        0.6, ge=0, description="Size of the model the service runs, in billions of parameters"
    )

    llm_ledger_path: str = Field(
        "var/llm_ledger.jsonl",
        description="Append-only JSONL record of every model call, for offline analysis",
    )
    # Project root for making source file paths relative in the ledger
    # Defaults to /app in production containers (where the code is mounted in the image)
    project_root: str = Field(
        "/app",
        description="Project root directory for relative source file paths in ledger",
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

    app_env: str = Field("dev", description="dev | demo | prod")
    frontend_origin: str = Field(
        "http://localhost:3000", description="Allowed CORS origin for the browser app"
    )

    # Real sign-in. Empty by default, and an empty provider is simply not offered rather
    # than offered and broken: a deployment with none configured falls back to the dev
    # picker, which app.main only mounts outside production. So a production deployment
    # with no provider configured has no way in at all, which is the correct failure.
    oauth_microsoft_client_id: str = Field("", description="Entra application (client) id")
    oauth_microsoft_client_secret: str = Field("", description="Entra client secret value")
    oauth_microsoft_tenant: str = Field(
        "",
        description="Entra directory (tenant) id. Empty means 'common', which admits any "
        "Microsoft account; name the tenant to admit only the plant's directory.",
    )
    oauth_google_client_id: str = Field("", description="Google OAuth client id")
    oauth_google_client_secret: str = Field("", description="Google OAuth client secret")
    # No default, deliberately. A shared fallback would mean every deployment that forgot
    # to set one could mint sessions for every other.
    session_secret: str = Field(
        "", description="Signing key for the session cookie. Required for real sign-in."
    )
    public_base_url: str = Field(
        "http://localhost:8000",
        description="This API's public origin, used to build the OAuth redirect URI. It "
        "must match the redirect registered with the provider exactly.",
    )
    log_level: str = Field(
        "INFO",
        description="Level for the app.* loggers. INFO keeps the per-call token-usage "
        "records ARCHITECTURE.md requires; raise to WARNING to quieten them.",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
