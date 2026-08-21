from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.factory import apply_runtime_overrides
from app.settings.repository import SettingsRepository
from app.settings.schemas import SettingsRead, SettingsUpdate


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = SettingsRepository(session)

    async def read(self) -> SettingsRead:
        row = await self.repo.get()
        if row is None:
            return SettingsRead(tier_config={})
        return self.repo.to_read(row)

    async def update(self, data: SettingsUpdate) -> SettingsRead:
        row = await self.repo.upsert(data)
        apply_runtime_overrides(row.tier_config)
        return self.repo.to_read(row)
