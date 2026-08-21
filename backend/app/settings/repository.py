from sqlalchemy.ext.asyncio import AsyncSession

from app.settings.models import AppSettings
from app.settings.schemas import SettingsRead, SettingsUpdate, TierConfig


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self) -> AppSettings | None:
        return await self.session.get(AppSettings, "singleton")

    async def upsert(self, data: SettingsUpdate) -> AppSettings:
        row = await self.get()
        if row is None:
            row = AppSettings(id="singleton", tier_config={})
            self.session.add(row)
        for tier, cfg in data.tier_config.items():
            existing = row.tier_config.get(tier, {})
            for key, value in cfg.model_dump(exclude_none=True).items():
                existing[key] = value
            row.tier_config[tier] = existing
        return row

    @staticmethod
    def to_read(row: AppSettings | None) -> SettingsRead:
        raw = row.tier_config if row else {}
        return SettingsRead(
            tier_config={
                tier: TierConfig(**cfg) if isinstance(cfg, dict) else TierConfig()
                for tier, cfg in raw.items()
            }
        )
