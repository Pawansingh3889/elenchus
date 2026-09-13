"""Admin routes for the conduct prompt: list versions, read one, save a new one, activate."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.db.session import get_session
from app.prompts.schemas import (
    PromptActivate,
    PromptBodyRead,
    PromptFamilyRead,
    PromptVersionWrite,
)
from app.prompts.service import PromptAdminService
from app.users.models import User

router = APIRouter(prefix="/api/v1/admin/prompts", tags=["prompts"])


@router.get("/{family}", response_model=PromptFamilyRead)
async def family(
    family: str,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> PromptFamilyRead:
    return await PromptAdminService(session).family(admin, family)


@router.get("/{family}/versions/{name}", response_model=PromptBodyRead)
async def version_body(
    family: str,
    name: str,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> PromptBodyRead:
    return await PromptAdminService(session).body(admin, family, name)


@router.post("/{family}/versions", response_model=PromptFamilyRead, status_code=201)
async def save_version(
    family: str,
    payload: PromptVersionWrite,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> PromptFamilyRead:
    return await PromptAdminService(session).save(admin, family, payload.body, payload.note)


@router.post("/{family}/activate", response_model=PromptFamilyRead)
async def activate(
    family: str,
    payload: PromptActivate,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> PromptFamilyRead:
    return await PromptAdminService(session).activate(admin, family, payload.name)
