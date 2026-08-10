"""Queries for reading completed and in-flight runs back out."""

from typing import Any
from uuid import UUID

from sqlalchemy import Row, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.runs.enums import RunStatus
from app.runs.models import SurveyRun
from app.templates.models import SurveyTemplate, SurveyTemplateVersion
from app.users.models import User

ResultRow = Row[tuple[SurveyRun, SurveyTemplateVersion, User]]


class ResultsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_template(self, template_id: UUID) -> list[ResultRow]:
        stmt = (
            select(SurveyRun, SurveyTemplateVersion, User)
            .join(SurveyTemplateVersion, SurveyRun.template_version_id == SurveyTemplateVersion.id)
            .join(User, SurveyRun.respondent_id == User.id)
            .where(SurveyTemplateVersion.template_id == template_id)
            .order_by(SurveyRun.started_at.desc())
            .options(selectinload(SurveyRun.answers))
        )
        return list((await self.session.execute(stmt)).all())

    async def dashboard_rows(self, author_id: UUID) -> list[Row[Any]]:
        """Every survey this author owns, with its run counts, in one query.

        One query rather than one per survey. The obvious wrong turn here is to list the
        templates and then count each one's runs, which is an N+1 that looks fine against
        the five surveys a developer has and falls over on the hundredth.

        Aggregated in the database rather than by loading runs and counting them in
        Python, for the same reason: the counts are the whole payload, and a survey with
        ten thousand runs should cost the same to summarise as one with ten.

        Outer joins throughout, so a survey that has been published but never answered,
        or never even published, appears with zeros rather than vanishing from the
        author's own dashboard.
        """
        started = func.count(SurveyRun.id)
        completed = func.count(SurveyRun.id).filter(SurveyRun.status == RunStatus.completed)
        in_progress = func.count(SurveyRun.id).filter(SurveyRun.status == RunStatus.in_progress)
        abandoned = func.count(SurveyRun.id).filter(SurveyRun.status == RunStatus.abandoned)
        # People, alongside runs. The counts above are of *runs*, which is the right
        # answer to "how is this survey going" and the wrong one to "how many of the
        # people it was for have answered": one respondent with four runs read as four
        # people until the engine started refusing a second. `respondent_id` is already
        # on the run row, so this needs no join and cannot fan the run counts out.
        people_started = func.count(distinct(SurveyRun.respondent_id))
        people_completed = func.count(distinct(SurveyRun.respondent_id)).filter(
            SurveyRun.status == RunStatus.completed
        )

        stmt = (
            select(
                SurveyTemplate,
                started.label("started"),
                completed.label("completed"),
                in_progress.label("in_progress"),
                abandoned.label("abandoned"),
                people_started.label("people_started"),
                people_completed.label("people_completed"),
                func.max(SurveyRun.started_at).label("last_started_at"),
                func.max(SurveyRun.completed_at).label("last_completed_at"),
            )
            .outerjoin(
                SurveyTemplateVersion,
                SurveyTemplateVersion.template_id == SurveyTemplate.id,
            )
            .outerjoin(SurveyRun, SurveyRun.template_version_id == SurveyTemplateVersion.id)
            .where(SurveyTemplate.created_by == author_id)
            .group_by(SurveyTemplate.id)
            .order_by(SurveyTemplate.updated_at.desc())
        )
        return list((await self.session.execute(stmt)).all())

    async def get_detail(self, run_id: UUID) -> ResultRow | None:
        stmt = (
            select(SurveyRun, SurveyTemplateVersion, User)
            .join(SurveyTemplateVersion, SurveyRun.template_version_id == SurveyTemplateVersion.id)
            .join(User, SurveyRun.respondent_id == User.id)
            .where(SurveyRun.id == run_id)
            .options(selectinload(SurveyRun.answers), selectinload(SurveyRun.messages))
        )
        return (await self.session.execute(stmt)).first()
