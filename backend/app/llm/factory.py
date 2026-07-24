"""Build the LLM client the app should use, from settings.

Assembles an ordered failover chain: the Anthropic primary first (when its key is set),
then each enabled backup — the first backup, then the second. Resolution:

- Two or more tiers configured -> a ``FailoverLLM`` chaining them in that order.
- Exactly one tier configured   -> that client alone.
- Nothing configured            -> an Anthropic client, which fails loudly at construction.

Kept out of ``client.py`` so that module has no import cycle with ``backup``/``failover``.
"""

from app.config import get_settings
from app.llm.backup import OpenAICompatibleLLMClient
from app.llm.client import LLMClient, LLMProtocol
from app.llm.failover import FailoverLLM


def get_llm() -> LLMProtocol:
    settings = get_settings()

    chain: list[LLMProtocol] = []
    if settings.anthropic_api_key:
        chain.append(LLMClient())
    if settings.llm_backup_enabled:
        chain.append(
            OpenAICompatibleLLMClient(
                base_url=settings.llm_backup_base_url,
                api_key=settings.llm_backup_api_key,
                model=settings.llm_backup_model,
                timeout_seconds=settings.llm_backup_timeout_seconds,
            )
        )
    if settings.llm_backup2_enabled:
        chain.append(
            OpenAICompatibleLLMClient(
                base_url=settings.llm_backup2_base_url,
                api_key=settings.llm_backup2_api_key,
                model=settings.llm_backup2_model,
                timeout_seconds=settings.llm_backup2_timeout_seconds,
            )
        )

    if not chain:
        # Nothing configured: constructing the Anthropic client raises the loud
        # "ANTHROPIC_API_KEY is not configured" error, rather than degrading silently.
        return LLMClient()
    if len(chain) == 1:
        return chain[0]
    return FailoverLLM(*chain)
