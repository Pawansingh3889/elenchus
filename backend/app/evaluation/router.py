"""The evaluation lens: the labelling queue, labels, the faithfulness report, judging."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.db.session import get_session
from app.evaluation.schemas import (
    EvalItem,
    FaithfulnessReport,
    JudgeRunRead,
    LabelRequest,
    Source,
)
from app.evaluation.service import EvaluationService
from app.users.models import User

router = APIRouter(prefix="/api/v1/lens/evaluation", tags=["lens-evaluation"])


@router.get("/items", response_model=list[EvalItem])
async def items(
    source: Source = Query(...),
    unlabelled: bool = Query(False),
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> list[EvalItem]:
    return await EvaluationService(session).items(admin, source, unlabelled)


@router.put("/items/{key}/label", response_model=EvalItem)
async def label(
    key: str,
    request: LabelRequest,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> EvalItem:
    return await EvaluationService(session).label(admin, key, request)


@router.get("/faithfulness", response_model=FaithfulnessReport)
async def faithfulness(
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> FaithfulnessReport:
    return await EvaluationService(session).faithfulness(admin)


@router.post("/runs/{run_id}/judge", response_model=JudgeRunRead)
async def judge_run(
    run_id: UUID,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> JudgeRunRead:
    return await EvaluationService(session).judge_run(admin, run_id)
