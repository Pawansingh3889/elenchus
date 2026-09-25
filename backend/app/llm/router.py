from fastapi import APIRouter, Depends, HTTPException, Path

from app.auth.dependencies import require_admin
from app.llm.eval_corpus import get_eval_accuracy_report
from app.llm.schemas import EvalAccuracyReport, LlmEntry, LlmLedger, LlmReport
from app.llm.service import get_llm_ledger, get_llm_report, get_llm_run_entries
from app.users.models import User

router = APIRouter(prefix="/api/v1/admin/llm", tags=["llm-admin"])


@router.get("/report", response_model=LlmReport)
async def llm_report(
    viewer: User = Depends(require_admin),
) -> LlmReport:
    return get_llm_report(viewer.workspace_id)


@router.get("/eval-accuracy", response_model=EvalAccuracyReport)
async def llm_eval_accuracy(
    _: User = Depends(require_admin),
) -> EvalAccuracyReport:
    """The judge's verdicts on the captured live-run corpus, not live production
    traffic. See app.llm.eval_corpus for what that distinction means."""
    return get_eval_accuracy_report()


@router.get("/ledger", response_model=LlmLedger)
async def llm_ledger(
    viewer: User = Depends(require_admin),
) -> LlmLedger:
    return get_llm_ledger(viewer.workspace_id)


@router.get("/run/{run_id}", response_model=list[LlmEntry])
async def llm_run_entries(
    run_id: str = Path(..., min_length=1),
    viewer: User = Depends(require_admin),
) -> list[LlmEntry]:
    entries = get_llm_run_entries(run_id, viewer.workspace_id)
    if not entries:
        raise HTTPException(status_code=404, detail="No ledger entries found for this run")
    return entries
