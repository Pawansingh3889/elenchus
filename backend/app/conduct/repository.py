"""All run, answer, and transcript queries."""

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.runs.enums import AnswerKind, RunStatus
from app.runs.models import Answer, RunMessage, SurveyRun
from app.templates.enums import SurveyAudience, TemplateStatus
from app.templates.models import SurveyTemplate

# Postgres SQLSTATE for "could not obtain lock" under FOR UPDATE NOWAIT.
LOCK_NOT_AVAILABLE = "55P03"


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, run: SurveyRun) -> None:
        self.session.add(run)

    def add_answer(self, answer: Answer) -> None:
        self.session.add(answer)

    def add_message(self, message: RunMessage) -> None:
        self.session.add(message)

    async def delete(self, run: SurveyRun) -> None:
        """Erase a run, and with it every answer and message it holds.

        Through the ORM rather than a bulk DELETE, so the cascades declared on the
        relationships actually run: the database has ON DELETE CASCADE on both children
        too, and either route works, but a bulk delete would leave the identity map
        holding rows that no longer exist for the rest of the request.
        """
        await self.session.delete(run)

    async def try_lock(self, run_id: UUID) -> bool:
        """Take the run's row lock for this transaction, or report it already held.

        ``NOWAIT`` rather than a plain wait: the lock is held across a model call, so a
        waiting request would block for the length of that call and then process a
        message the respondent almost certainly sent by double-clicking. Failing fast
        lets the caller say so instead.

        Selects only the id, so the row lock never has to contend with the eager loads
        ``get`` performs.
        """
        stmt = select(SurveyRun.id).where(SurveyRun.id == run_id).with_for_update(nowait=True)
        try:
            await self.session.execute(stmt)
        except DBAPIError as exc:
            # 55P03 lock_not_available is the only NOWAIT outcome that means "busy".
            # Anything else is a real database failure and must not be swallowed.
            if getattr(exc.orig, "sqlstate", None) != LOCK_NOT_AVAILABLE:
                raise
            # Postgres aborts the transaction on a failed NOWAIT, so the session is
            # unusable until it is rolled back.
            await self.session.rollback()
            return False
        return True

    async def get(self, run_id: UUID) -> SurveyRun | None:
        stmt = (
            select(SurveyRun)
            .where(SurveyRun.id == run_id)
            .options(selectinload(SurveyRun.answers), selectinload(SurveyRun.messages))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_template(self, template_id: UUID) -> SurveyTemplate | None:
        """The survey a run is being conducted against, with its questions loaded.

        Replaces the pair of version reads this used to carry. `conduct` keeps its own
        query rather than borrowing `templates`': it reads a survey in order to conduct
        it, and owns that read.
        """
        stmt = (
            select(SurveyTemplate)
            .where(SurveyTemplate.id == template_id)
            .options(selectinload(SurveyTemplate.questions))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def template_gate(
        self, template_id: UUID
    ) -> tuple[TemplateStatus, SurveyAudience, UUID, UUID | None] | None:
        """The four facts conducting needs about a survey before it will start a run:
        whether it is still open, who it is for, which one person if it names one, and who
        owns it. None if no such survey.

        One query returning four columns rather than four calls or a whole template.
        Conduct has no business holding an author's aggregate, and starting a run should
        not drag the questions across to read a status and an audience.
        """
        stmt = select(
            SurveyTemplate.status,
            SurveyTemplate.audience,
            SurveyTemplate.created_by,
            SurveyTemplate.audience_user_id,
        ).where(SurveyTemplate.id == template_id)
        row = (await self.session.execute(stmt)).first()
        return (row[0], row[1], row[2], row[3]) if row else None

    async def template_status(self, template_id: UUID) -> TemplateStatus | None:
        """The template's status, or None if there is no such template.

        Selects the one column rather than loading the template: conduct has no business
        holding an author's aggregate, and starting a run should not pull its questions
        across just to read a status it will compare once.
        """
        stmt = select(SurveyTemplate.status).where(SurveyTemplate.id == template_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def count_answers(self, run_id: UUID, question_id: UUID, kind: AnswerKind) -> int:
        stmt = (
            select(func.count())
            .select_from(Answer)
            .where(Answer.run_id == run_id, Answer.question_id == question_id, Answer.kind == kind)
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def scripted_value(self, run_id: UUID, question_id: UUID) -> dict[str, Any] | None:
        """What this run already recorded against the author's own question, or None.

        Read so a follow-up's answer can be compared against it: a probe that comes back
        with the value already banked has answered the scripted question a second time,
        not the one the model asked.
        """
        stmt = select(Answer.value).where(
            Answer.run_id == run_id,
            Answer.question_id == question_id,
            Answer.kind == AnswerKind.scripted,
        )
        value = (await self.session.execute(stmt)).scalars().first()
        return value if isinstance(value, dict) else None

    async def answered_already(self, template_id: UUID, respondent_id: UUID) -> SurveyRun | None:
        """This respondent's existing run of this survey, newest first, or None.

        Keyed on the template rather than the version it was published as. A run belongs
        to the survey it answered: republishing to fix a typo must not silently reopen the
        survey to everyone who has already been through it, and reissuing it deliberately
        is a new survey rather than a second version of the old one.

        Abandoned runs are excluded, so a run that is ever aged out stops standing in
        anyone's way. Nothing sets that status today, which is worth knowing rather than
        relying on.
        """
        stmt = (
            select(SurveyRun)
            .where(
                SurveyRun.template_id == template_id,
                SurveyRun.respondent_id == respondent_id,
                SurveyRun.status != RunStatus.abandoned,
            )
            # Completed first, so one finished run refuses a restart even if the
            # respondent has since opened another that is still in progress.
            .order_by(
                (SurveyRun.status == RunStatus.completed).desc(),
                SurveyRun.started_at.desc(),
            )
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def in_progress_for(self, respondent_id: UUID) -> list[tuple[SurveyRun, UUID, str]]:
        """This respondent's unfinished runs, newest first, with the survey they belong to.

        Powers "continue where you left off": without it a respondent who closed the tab
        can only press Start again, which opens a *second* run and leaves the first
        stranded in the author's results as an abandoned half-answer.
        """
        stmt = (
            select(SurveyRun, SurveyRun.template_id, SurveyTemplate.title)
            .join(SurveyTemplate, SurveyRun.template_id == SurveyTemplate.id)
            .where(
                SurveyRun.respondent_id == respondent_id,
                SurveyRun.status == RunStatus.in_progress,
            )
            .order_by(SurveyRun.started_at.desc())
            .options(selectinload(SurveyRun.answers))
        )
        rows = (await self.session.execute(stmt)).all()
        # The third column is the survey's title, selected directly. It used to be the
        # frozen definition, out of which the title had to be dug with a default for the
        # case where the document had none.
        return [(r[0], r[1], r[2]) for r in rows]
