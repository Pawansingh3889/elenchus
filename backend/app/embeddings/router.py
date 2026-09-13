"""The embedding lens: answer map, themes, near duplicates, and the grounding measurement."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.db.session import get_session
from app.embeddings.schemas import AnswerMap, DuplicateReport, GroundingReport, ThemeReport
from app.embeddings.service import EmbeddingService
from app.users.models import User

router = APIRouter(prefix="/api/v1/lens", tags=["lens-embeddings"])


@router.get("/surveys/{survey_id}/answer-map", response_model=AnswerMap)
async def answer_map(
    survey_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> AnswerMap:
    return await EmbeddingService(session).answer_map(admin, survey_id)


@router.get("/surveys/{survey_id}/themes", response_model=ThemeReport)
async def themes(
    survey_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> ThemeReport:
    return await EmbeddingService(session).themes(admin, survey_id)


@router.get("/surveys/{survey_id}/duplicates", response_model=DuplicateReport)
async def duplicates(
    survey_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> DuplicateReport:
    return await EmbeddingService(session).duplicates(admin, survey_id)


@router.get("/grounding", response_model=GroundingReport)
async def grounding(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> GroundingReport:
    return await EmbeddingService(session).grounding(admin)
