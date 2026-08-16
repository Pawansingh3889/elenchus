"""All template, question, and version queries."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.runs.enums import RunStatus
from app.runs.models import SurveyRun
from app.templates.enums import TemplateStatus
from app.templates.models import SurveyQuestion, SurveyTemplate


class TemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, template: SurveyTemplate) -> None:
        self.session.add(template)

    async def get(self, template_id: UUID) -> SurveyTemplate | None:
        stmt = (
            select(SurveyTemplate)
            .where(SurveyTemplate.id == template_id)
            .options(selectinload(SurveyTemplate.questions))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_summaries(
        self,
        status: TemplateStatus | None,
        created_by: UUID | None = None,
        created_by_in: set[UUID] | None = None,
    ) -> list[tuple[SurveyTemplate, int]]:
        counts = (
            select(SurveyQuestion.template_id, func.count().label("n"))
            .group_by(SurveyQuestion.template_id)
            .subquery()
        )
        stmt = (
            select(SurveyTemplate, func.coalesce(counts.c.n, 0))
            .outerjoin(counts, counts.c.template_id == SurveyTemplate.id)
            .order_by(SurveyTemplate.updated_at.desc())
        )
        if status is not None:
            stmt = stmt.where(SurveyTemplate.status == status)
        if created_by is not None:
            stmt = stmt.where(SurveyTemplate.created_by == created_by)
        if created_by_in is not None:
            # An empty set means nobody, and must return nothing rather than everything.
            # `IN ()` is what SQLAlchemy renders for that, which is the honest answer;
            # skipping the clause when the set is empty would be the dangerous one.
            stmt = stmt.where(SurveyTemplate.created_by.in_(created_by_in))
        rows = (await self.session.execute(stmt)).all()
        return [(row[0], int(row[1])) for row in rows]

    async def delete(self, template: SurveyTemplate) -> None:
        await self.session.delete(template)

    async def completed_by(self, respondent_id: UUID) -> set[UUID]:
        """Templates this person has already finished.

        The respondent's list is an invitation, and after one-answer-per-person a Start
        button on a survey they have completed is a button that can only 409. A run now
        names its survey directly, so this is a read of `survey_runs` rather than the
        join through versions it used to be.
        """
        stmt = (
            select(SurveyRun.template_id)
            .where(
                SurveyRun.respondent_id == respondent_id,
                SurveyRun.status == RunStatus.completed,
            )
            .distinct()
        )
        return set((await self.session.execute(stmt)).scalars().all())

    async def list_published(self) -> list[SurveyTemplate]:
        """Published surveys, newest first, with their questions loaded.

        It used to return the survey beside the frozen definition a respondent would be
        asked, because a draft kept evolving after publication and counting its questions
        advertised a survey that did not exist yet: three questions on the home page, two
        in the run. With versions gone there is one set of questions and that gap closes
        by construction, so this returns the survey and its callers read the questions
        off it.
        """
        stmt = (
            select(SurveyTemplate)
            .where(SurveyTemplate.status == TemplateStatus.published)
            .options(selectinload(SurveyTemplate.questions))
            .order_by(SurveyTemplate.updated_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())
