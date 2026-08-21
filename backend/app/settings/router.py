from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.db.session import get_session
from app.settings.schemas import SettingsRead, SettingsUpdate
from app.settings.service import SettingsService
from app.users.models import User

router = APIRouter(prefix="/api/v1/admin/settings", tags=["admin-settings"])


@router.get("", response_model=SettingsRead)
async def read_settings(
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> SettingsRead:
    return await SettingsService(session).read()


@router.patch("", response_model=SettingsRead)
async def update_settings(
    data: SettingsUpdate,
    _: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> SettingsRead:
    return await SettingsService(session).update(data)
