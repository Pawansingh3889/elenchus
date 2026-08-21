from fastapi import APIRouter, Depends, HTTPException, Path

from app.auth.dependencies import require_admin
from app.llm.schemas import LlmEntry, LlmReport
from app.llm.service import get_llm_report, get_llm_run_entries
from app.users.models import User

router = APIRouter(prefix="/api/v1/admin/llm", tags=["llm-admin"])


@router.get("/report", response_model=LlmReport)
async def llm_report(
    _: User = Depends(require_admin),
) -> LlmReport:
    return get_llm_report()


@router.get("/run/{run_id}", response_model=list[LlmEntry])
async def llm_run_entries(
    run_id: str = Path(..., min_length=1),
    _: User = Depends(require_admin),
) -> list[LlmEntry]:
    entries = get_llm_run_entries(run_id)
    if not entries:
        raise HTTPException(status_code=404, detail="No ledger entries found for this run")
    return entries
