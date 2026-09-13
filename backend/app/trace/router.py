"""The lens: admin-only reads of the trace, for the pages that explain the model."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.db.session import get_session
from app.trace.schemas import LensStrip, SpanRead, TracedRun
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
