"""The interpretability lens reads. Administrators only."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.db.session import get_session
from app.interp.schemas import CapturedAsk, InterpStatus, StoredAnalysis
from app.interp.service import InterpService
from app.users.models import User

router = APIRouter(prefix="/api/v1/lens/interp", tags=["lens-interp"])


@router.get("/status", response_model=InterpStatus)
async def status(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> InterpStatus:
    return await InterpService(session).status(admin)


@router.get("/asks", response_model=list[CapturedAsk])
async def asks(
    survey_id: UUID | None = Query(None),
    run_id: UUID | None = Query(None),
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[CapturedAsk]:
    return await InterpService(session).asks(admin, survey_id, run_id)


@router.get("/asks/{span_id}", response_model=StoredAnalysis)
async def analysis(
    span_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> StoredAnalysis:
    return await InterpService(session).analysis(admin, span_id)


@router.post("/asks/{span_id}/analyse", response_model=StoredAnalysis)
async def analyse(
    span_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> StoredAnalysis:
    return await InterpService(session).analyse(admin, span_id)


@router.post("/asks/{span_id}/attribute", response_model=StoredAnalysis)
async def attribute(
    span_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> StoredAnalysis:
    return await InterpService(session).attribute(admin, span_id)
