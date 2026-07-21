"""Results routes: an author reading responses to their survey."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_author
from app.db.session import get_session
from app.runs.schemas import RunDetail, RunSummary
from app.runs.service import ResultsService
from app.users.models import User

router = APIRouter(prefix="/api/v1/templates", tags=["results"])


@router.get("/{template_id}/runs", response_model=list[RunSummary])
async def list_runs(
    template_id: UUID,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> list[RunSummary]:
    return await ResultsService(session).list_runs(template_id, author)


@router.get("/{template_id}/runs/{run_id}", response_model=RunDetail)
async def get_run(
    template_id: UUID,
    run_id: UUID,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> RunDetail:
    return await ResultsService(session).get_run(template_id, run_id, author)
