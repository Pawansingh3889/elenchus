"""Reading run results back for authors.

Deliberately separate from the conduct engine: conducting is respondent-owned and
refuses anyone else, while results are author-facing and cross-respondent.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import NotFoundError
from app.runs.enums import AnswerKind
from app.runs.models import SurveyRun
from app.runs.repository import ResultsRepository
from app.runs.schemas import AnswerRead, MessageRead, RunDetail, RunSummary
from app.templates.models import SurveyTemplateVersion
from app.templates.repository import TemplateRepository
from app.users.models import User


class ResultsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ResultsRepository(session)
        self.templates = TemplateRepository(session)

    async def list_runs(self, template_id: UUID, author: User) -> list[RunSummary]:
        await self._owned_or_404(template_id, author)
        rows = await self.repo.list_for_template(template_id)
        return [_summary(run, version, user) for run, version, user in rows]

    async def get_run(self, template_id: UUID, run_id: UUID, author: User) -> RunDetail:
        await self._owned_or_404(template_id, author)
        row = await self.repo.get_detail(run_id)
        if row is None:
            raise NotFoundError("Run not found.")
        run, version, user = row
        if version.template_id != template_id:
            raise NotFoundError("That run belongs to a different template.")
        return RunDetail(
            id=run.id,
            respondent_name=user.display_name,
            status=run.status,
            version=version.version,
            started_at=run.started_at,
            completed_at=run.completed_at,
            messages=[MessageRead.model_validate(m) for m in run.messages],
            answers=[AnswerRead.model_validate(a) for a in run.answers],
        )

    async def _owned_or_404(self, template_id: UUID, author: User) -> None:
        """Responses carry respondent names and verbatim transcripts, so they are
        readable only by the author who created the survey. Someone else's template
        reads as absent rather than forbidden."""
        template = await self.templates.get(template_id)
        if template is None or template.created_by != author.id:
            raise NotFoundError("Template not found.")


def _summary(run: SurveyRun, version: SurveyTemplateVersion, user: User) -> RunSummary:
    return RunSummary(
        id=run.id,
        respondent_name=user.display_name,
        status=run.status,
        version=version.version,
        answered=sum(1 for a in run.answers if a.kind is AnswerKind.scripted),
        total=len(version.definition["questions"]),
        started_at=run.started_at,
        completed_at=run.completed_at,
    )
