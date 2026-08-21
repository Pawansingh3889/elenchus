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


def _client_for(settings: Settings, prefix: str, tier: int) -> OpenAICompatibleLLMClient:
    return OpenAICompatibleLLMClient(
        base_url=getattr(settings, f"{prefix}_base_url"),
        api_key=getattr(settings, f"{prefix}_api_key"),
        model=getattr(settings, f"{prefix}_model"),
        timeout_seconds=getattr(settings, f"{prefix}_timeout_seconds"),
        # The tier number the client is told is its position in the settings, not its
        # position in the chain: with tiers 1 and 3 enabled, the second client is still
        # tier 3, and pricing it as tier 2 would bill it at another provider's rate.
        tier=tier,
        # Opt-in: only a caching-capable provider (e.g. OpenRouter/Anthropic) should set
        # this, or OpenAI answers a 400 and drops out of the chain.
        prompt_cache=getattr(settings, f"{prefix}_prompt_cache", False),
    )


def get_llm() -> LLMProtocol:
    settings = get_settings()

    chain: list[LLMProtocol] = [
        _client_for(settings, prefix, tier)
        for tier, prefix in enumerate(TIER_PREFIXES, start=1)
        if getattr(settings, f"{prefix}_enabled")
    ]

    if not chain:
        # The one case with nothing to fall back to. Said plainly here rather than
        # letting a caller discover an empty chain further down.
        raise LLMError(
            "No LLM tier is configured. Enable at least one of LLM_TIER1..LLM_TIER4 "
            "with its base URL and model."
        )
    if len(chain) == 1:
        return chain[0]
    return FailoverLLM(*chain)
