"""The lens: admin-only reads of the trace, for the pages that explain the model."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.db.session import get_session
from app.trace.schemas import AttemptRow, DecisionRow, LensStrip, SpanRead, TracedRun
from app.trace.service import LensService
from app.users.models import User

router = APIRouter(prefix="/api/v1/lens", tags=["lens"])


@router.get("/runs", response_model=list[TracedRun])
async def traced_runs(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[TracedRun]:
    return await LensService(session).runs(admin)


@router.get("/runs/{run_id}/spans", response_model=list[SpanRead])
async def run_spans(
    run_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[SpanRead]:
    return await LensService(session).spans(run_id, admin)


@router.get("/strip", response_model=LensStrip)
async def strip(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> LensStrip:
    return await LensService(session).strip(admin)


@router.get("/attempts", response_model=list[AttemptRow])
async def attempts(
    survey_id: UUID | None = Query(None),
    run_id: UUID | None = Query(None),
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[AttemptRow]:
    return await LensService(session).attempts(admin, survey_id, run_id)


@router.get("/decisions", response_model=list[DecisionRow])
async def decisions(
    survey_id: UUID | None = Query(None),
    run_id: UUID | None = Query(None),
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[DecisionRow]:
    return await LensService(session).decisions(admin, survey_id, run_id)
