"""Queries for reading completed and in-flight runs back out."""

from typing import Any
from uuid import UUID

from sqlalchemy import Row, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.runs.enums import RunStatus
from app.runs.models import SurveyRun
from app.runs.schemas import RespondentRow
from app.templates.models import SurveyTemplate
from app.users.models import User

ResultRow = Row[tuple[SurveyRun, SurveyTemplate, User]]


class ResultsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_template(self, template_id: UUID) -> list[ResultRow]:
        stmt = (
            select(SurveyRun, SurveyTemplate, User)
            .join(SurveyTemplate, SurveyRun.template_id == SurveyTemplate.id)
            .join(User, SurveyRun.respondent_id == User.id)
            .where(SurveyRun.template_id == template_id)
            .order_by(SurveyRun.started_at.desc())
            # The template's questions come with it: the caller reads them off this row,
            # and without this that is a lazy load in an async session, which raises
            # rather than quietly issuing a query.
            .options(selectinload(SurveyRun.answers), selectinload(SurveyTemplate.questions))
        )
        return list((await self.session.execute(stmt)).all())

    async def respondent_numbers(self, template_id: UUID) -> dict[UUID, int]:
        """Each respondent's number within this survey, counting from one.

        The author needs to tell one respondent's answers from another's and to follow a
        single person across the list, the run detail and the recap. A name does all of
        that and one thing more, which is the thing that was agreed against: it tells the
        author who said it.

        Ordered by the respondent's first run rather than by name or id, so the numbers
        read as the order people answered in, and tie-broken on the id so two runs
        started in the same transaction cannot swap numbers between requests. Stability
        is the whole value: a label that renumbered on refresh would be worse than none,
        because the author would trust it and be wrong.

        Scoped to the template, so the same person is Respondent 2 in one survey and
        Respondent 7 in another. That is deliberate. A number stable across surveys would
        be a pseudonymous identity to correlate answers with, which is what the author is
        not supposed to have.
        """
        stmt = (
            select(SurveyRun.respondent_id)
            .join(SurveyTemplate, SurveyRun.template_id == SurveyTemplate.id)
            .where(SurveyRun.template_id == template_id)
            .group_by(SurveyRun.respondent_id)
            .order_by(func.min(SurveyRun.started_at), SurveyRun.respondent_id)
        )
        rows = (await self.session.execute(stmt)).scalars().all()
        return {respondent_id: number for number, respondent_id in enumerate(rows, start=1)}

    async def dashboard_rows(self, author_ids: set[UUID]) -> list[Row[Any]]:
        """Every survey these authors own, with its run counts, in one query.

        A set rather than one id, because a survey belongs to a department as well as to
        the person who made it: a colleague has to see it, and a survey they did not
        create is not in `created_by = me` for any amount of filtering afterwards.

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
            # One outer join where there were two. A run named a version and a version
            # named a survey, so counting a survey's runs meant hopping through a table
            # that existed only to be hopped through.
            .outerjoin(SurveyRun, SurveyRun.template_id == SurveyTemplate.id)
            .where(SurveyTemplate.created_by.in_(author_ids))
            .group_by(SurveyTemplate.id)
            .order_by(SurveyTemplate.updated_at.desc())
        )
        return list((await self.session.execute(stmt)).all())

    async def get_detail(self, run_id: UUID) -> ResultRow | None:
        stmt = (
            select(SurveyRun, SurveyTemplate, User)
            .join(SurveyTemplate, SurveyRun.template_id == SurveyTemplate.id)
            .join(User, SurveyRun.respondent_id == User.id)
            .where(SurveyRun.id == run_id)
            .options(
                selectinload(SurveyRun.answers),
                selectinload(SurveyRun.messages),
                # The caller reads the survey's questions off this row. Without it that
                # is a lazy load in an async session, which raises rather than querying.
                selectinload(SurveyTemplate.questions),
            )
        )
        return (await self.session.execute(stmt)).first()

    async def respondents_for_template(self, template_id: UUID) -> list[RespondentRow]:
        """All respondents for a survey with their participation summary and current status.

        Returns one row per respondent, aggregating their runs and showing their latest
        session status for real-time tracking. Used by the dashboard to show who is
        currently active on a survey.
        """
        # Aggregate respondent-level statistics
        total_runs = func.count(SurveyRun.id)
        completed_runs = func.count(SurveyRun.id).filter(SurveyRun.status == RunStatus.completed)
        in_progress_runs = func.count(SurveyRun.id).filter(
            SurveyRun.status == RunStatus.in_progress
        )
        abandoned_runs = func.count(SurveyRun.id).filter(SurveyRun.status == RunStatus.abandoned)

        # Get respondents with their run aggregates
        respondent_stats = (
            select(
                SurveyRun.respondent_id,
                User.display_name,
                total_runs.label("total_runs"),
                completed_runs.label("completed_runs"),
                in_progress_runs.label("in_progress_runs"),
                abandoned_runs.label("abandoned_runs"),
                func.min(SurveyRun.started_at).label("first_started_at"),
                func.max(SurveyRun.started_at).label("last_started_at"),
                func.max(SurveyRun.completed_at).label("last_completed_at"),
            )
            .join(User, SurveyRun.respondent_id == User.id)
            .where(SurveyRun.template_id == template_id)
            .group_by(SurveyRun.respondent_id, User.display_name)
            .order_by(func.min(SurveyRun.started_at), SurveyRun.respondent_id)
        )

        stats_rows = (await self.session.execute(respondent_stats)).all()

        # Get respondent numbers (matching the existing respondent_numbers logic)
        respondent_numbers = await self.respondent_numbers(template_id)

        # Get current active runs for each respondent
        active_runs_stmt = (
            select(
                SurveyRun.respondent_id,
                SurveyRun.id.label("current_run_id"),
                SurveyRun.status.label("current_status"),
                func.max(SurveyRun.started_at).label("last_activity_at"),
            )
            .where(SurveyRun.template_id == template_id)
            .where(SurveyRun.status == RunStatus.in_progress)
            .group_by(SurveyRun.respondent_id, SurveyRun.id, SurveyRun.status)
        )
        active_runs = (await self.session.execute(active_runs_stmt)).all()
        active_runs_by_respondent = {row.respondent_id: row for row in active_runs}

        # Build respondent rows
        respondents = []
        for row in stats_rows:
            respondent_id = row.respondent_id
            number = respondent_numbers.get(respondent_id, 0)
            respondent_label = f"Respondent {number}"

            active_run = active_runs_by_respondent.get(respondent_id)

            respondents.append(
                RespondentRow(
                    respondent_id=respondent_id,
                    respondent_label=respondent_label,
                    display_name=row.display_name,
                    total_runs=row.total_runs,
                    completed_runs=row.completed_runs,
                    in_progress_runs=row.in_progress_runs,
                    abandoned_runs=row.abandoned_runs,
                    first_started_at=row.first_started_at,
                    last_started_at=row.last_started_at,
                    last_completed_at=row.last_completed_at,
                    current_run_id=active_run.current_run_id if active_run else None,
                    current_status=active_run.current_status if active_run else None,
                    last_activity_at=active_run.last_activity_at if active_run else None,
                )
            )

        return respondents
