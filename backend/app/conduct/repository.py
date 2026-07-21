"""All run, answer, and transcript queries."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.runs.enums import AnswerKind
from app.runs.models import Answer, RunMessage, SurveyRun
from app.templates.models import SurveyTemplateVersion


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, run: SurveyRun) -> None:
        self.session.add(run)

    def add_answer(self, answer: Answer) -> None:
        self.session.add(answer)

    def add_message(self, message: RunMessage) -> None:
        self.session.add(message)

    async def get(self, run_id: UUID) -> SurveyRun | None:
        stmt = (
            select(SurveyRun)
            .where(SurveyRun.id == run_id)
            .options(selectinload(SurveyRun.answers), selectinload(SurveyRun.messages))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def latest_version(self, template_id: UUID) -> SurveyTemplateVersion | None:
        stmt = (
            select(SurveyTemplateVersion)
            .where(SurveyTemplateVersion.template_id == template_id)
            .order_by(SurveyTemplateVersion.version.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_version(self, version_id: UUID) -> SurveyTemplateVersion | None:
        return await self.session.get(SurveyTemplateVersion, version_id)

    async def count_answers(self, run_id: UUID, question_id: UUID, kind: AnswerKind) -> int:
        stmt = (
            select(func.count())
            .select_from(Answer)
            .where(Answer.run_id == run_id, Answer.question_id == question_id, Answer.kind == kind)
        )
        return int((await self.session.execute(stmt)).scalar_one())
