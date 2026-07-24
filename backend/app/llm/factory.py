"""Build the LLM client the app should use, from settings.

Resolution:
- Backup configured + primary key present -> Anthropic primary with backup failover.
- Only the backup configured               -> the backup alone.
- Only the primary key present             -> Anthropic alone (previous behaviour).
- Neither configured                       -> Anthropic client, which fails loudly at use.

Kept out of ``client.py`` so that module has no import cycle with ``backup``/``failover``.
"""

from app.config import get_settings
from app.llm.backup import OpenAICompatibleLLMClient
from app.llm.client import LLMClient, LLMProtocol
from app.llm.failover import FailoverLLM


def get_llm() -> LLMProtocol:
    settings = get_settings()

    backup: OpenAICompatibleLLMClient | None = None
    if settings.llm_backup_enabled:
        backup = OpenAICompatibleLLMClient(
            base_url=settings.llm_backup_base_url,
            api_key=settings.llm_backup_api_key,
            model=settings.llm_backup_model,
            timeout_seconds=settings.llm_backup_timeout_seconds,
        )

    if settings.anthropic_api_key:
        primary = LLMClient()
        return FailoverLLM(primary, backup) if backup is not None else primary

    if backup is not None:
        return backup

    # Neither is configured: return the primary so it raises the same loud error at use.
    return LLMClient()
