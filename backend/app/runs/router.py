"""Results routes: an author reading responses to their survey."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_author
from app.db.session import get_session
from app.runs.schemas import DashboardRow, RunDetail, RunSummary, SurveyReport
from app.runs.service import ResultsService
from app.runs.summary import RunSummaryContent, RunSummaryService
from app.runs.survey_summary import SurveyRecapStatus, SurveySummaryRead, SurveySummaryService
from app.users.models import User

router = APIRouter(prefix="/api/v1/templates", tags=["results"])

# Its own prefix rather than /api/v1/templates/dashboard. The templates router is
# registered first and owns /{template_id}, so a literal path added here would be matched
# as a template id and rejected as a malformed UUID, which is a confusing way to learn
# about route ordering across two modules.
dashboard_router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@dashboard_router.get("", response_model=list[DashboardRow])
async def dashboard(
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> list[DashboardRow]:
    """Every survey this author owns and how each is going, in one request."""
    return await ResultsService(session).dashboard(author)


@router.get("/{template_id}/runs", response_model=list[RunSummary])
async def list_runs(
    template_id: UUID,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> list[RunSummary]:
    return await ResultsService(session).list_runs(template_id, author)


@router.get("/{template_id}/report", response_model=SurveyReport)
async def survey_report(
    template_id: UUID,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> SurveyReport:
    """What the survey found, question by question. Declared before /{template_id}/runs
    is irrelevant here (different literal), but it is grouped with the other read
    endpoints for the same reason they are: one service call, shaped by the schema."""
    return await ResultsService(session).report(template_id, author)


@router.get("/{template_id}/summary", response_model=SurveyRecapStatus)
async def survey_recap(
    template_id: UUID,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> SurveyRecapStatus:
    """The recap this survey already has, if the results have not moved past it.

    Same path as the POST, different verb: reading a recap should not cost a model call,
    and until this existed generating one was the only way to see it, so a page that
    navigated away and back paid to read prose already sitting in the column.
    """
    return await SurveySummaryService(session).stored(template_id, author)


@router.post("/{template_id}/summary", response_model=SurveySummaryRead)
async def summarise_survey(
    template_id: UUID,
    refresh: bool = Query(False, description="Regenerate even if a current recap is stored."),
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> SurveySummaryRead:
    """What the whole survey found, across every completed response.

    Author-triggered for the reason the per-run summary is: a model call costs seconds
    and can fail, and neither belongs in the path of a page an author opens to read
    numbers. The stored recap is reused only while the version and the completed-run
    count are what they were when it was written, because a recap of eight responses
    served after twenty have arrived is not stale, it is wrong.
    """
    return await SurveySummaryService(session).summarise(template_id, author, refresh)


@router.get("/{template_id}/runs/{run_id}", response_model=RunDetail)
async def get_run(
    template_id: UUID,
    run_id: UUID,
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> RunDetail:
    return await ResultsService(session).get_run(template_id, run_id, author)


@router.post("/{template_id}/runs/{run_id}/summary", response_model=RunSummaryContent)
async def summarise_run(
    template_id: UUID,
    run_id: UUID,
    refresh: bool = Query(False, description="Regenerate even if a summary is stored."),
    author: User = Depends(require_author),
    session: AsyncSession = Depends(get_session),
) -> RunSummaryContent:
    """Summarise one completed run. Author-triggered rather than generated when the
    respondent finishes: a model call on the respondent's last turn would put LLM latency
    (and LLM failure) in the path of recording their final answer."""
    return await RunSummaryService(session).summarise(template_id, run_id, author, refresh)
