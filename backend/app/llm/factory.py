"""Build the LLM client the app should use, from settings.

Assembles an ordered failover chain from the enabled tiers, lowest number first.
Resolution:

- Two or more tiers enabled -> a ``FailoverLLM`` chaining them in tier order.
- Exactly one tier enabled   -> that client alone, with no wrapper.
- No tier enabled            -> a loud ``LLMError``, never a silent no-op.

Kept out of ``client.py`` so that module has no import cycle with
``openai_compatible``/``failover``.
"""

from app.config import Settings, get_settings
from app.llm.client import LLMError, LLMProtocol
from app.llm.failover import FailoverLLM
from app.llm.openai_compatible import OpenAICompatibleLLMClient

# Tier order is positional, not alphabetical: tier 1 serves every turn until it fails.
TIER_PREFIXES = ("llm_tier1", "llm_tier2", "llm_tier3", "llm_tier4")

_runtime_overrides: dict[str, dict[str, object]] = {}


def apply_runtime_overrides(overrides: dict[str, dict[str, object]]) -> None:
    global _runtime_overrides
    _runtime_overrides = {str(k): dict(v) for k, v in overrides.items()}


def _merged_settings() -> Settings:
    settings = get_settings()
    if not _runtime_overrides:
        return settings
    return Settings.model_validate(
        {
            **settings.model_dump(),
            **{
                f"{prefix}_{key}": value
                for tier, overrides in _runtime_overrides.items()
                for key, value in overrides.items()
                for prefix in [f"llm_tier{tier}"]
            },
        }
    )


def _client_for(settings: Settings, prefix: str, tier: int) -> OpenAICompatibleLLMClient:
    return OpenAICompatibleLLMClient(
        base_url=getattr(settings, f"{prefix}_base_url"),
        api_key=getattr(settings, f"{prefix}_api_key"),
        model=getattr(settings, f"{prefix}_model"),
        timeout_seconds=getattr(settings, f"{prefix}_timeout_seconds"),
        tier=tier,
        prompt_cache=getattr(settings, f"{prefix}_prompt_cache", False),
        max_completion_tokens=getattr(settings, f"{prefix}_max_completion_tokens", 4096),
    )


def get_llm() -> LLMProtocol:
    settings = _merged_settings()

    chain: list[LLMProtocol] = [
        _client_for(settings, prefix, tier)
        for tier, prefix in enumerate(TIER_PREFIXES, start=1)
        if getattr(settings, f"{prefix}_enabled")
    ]

    if not chain:
        raise LLMError(
            "No LLM tier is configured. Enable at least one of LLM_TIER1..LLM_TIER4 "
            "with its base URL and model."
        )
    if len(chain) == 1:
        return chain[0]
    return FailoverLLM(*chain)
