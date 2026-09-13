"""Every query the evaluation lens makes."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.evaluation.enums import LabelVerdict
from app.evaluation.models import AnswerLabel, CorpusLabel, JudgeRun, JudgeVerdict
from app.runs.models import Answer, RunMessage, SurveyRun
from app.templates.models import SurveyQuestion, SurveyTemplate
from app.trace.enums import SpanKind
from app.trace.models import LLMSpan


class EvaluationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def answers(
        self, answer_id: UUID | None = None
    ) -> list[tuple[Answer, SurveyQuestion | None, str]]:
        """Database answers, oldest first, with their question and survey title.

        The question is outer-joined: a question removed since the answer was recorded
        leaves the answer, and the answer is still worth labelling.
        """
        stmt = (
            select(Answer, SurveyQuestion, SurveyTemplate.title)
            .join(SurveyRun, SurveyRun.id == Answer.run_id)
            .join(SurveyTemplate, SurveyTemplate.id == SurveyRun.template_id)
            .outerjoin(SurveyQuestion, SurveyQuestion.id == Answer.question_id)
            .order_by(Answer.answered_at)
        )
        if answer_id is not None:
            stmt = stmt.where(Answer.id == answer_id)
        return [
            (answer, question, title)
            for answer, question, title in (await self.session.execute(stmt)).all()
        ]

    async def answers_for_run(self, run_id: UUID) -> list[Answer]:
        stmt = select(Answer).where(Answer.run_id == run_id).order_by(Answer.answered_at)
        return list((await self.session.scalars(stmt)).all())

    async def messages(self, run_ids: list[UUID]) -> list[RunMessage]:
        if not run_ids:
            return []
        stmt = (
            select(RunMessage).where(RunMessage.run_id.in_(run_ids)).order_by(RunMessage.created_at)
        )
        return list((await self.session.scalars(stmt)).all())

    async def run(self, run_id: UUID) -> SurveyRun | None:
        return await self.session.get(SurveyRun, run_id)

    async def answer_labels(self) -> dict[UUID, AnswerLabel]:
        return {row.answer_id: row for row in (await self.session.scalars(select(AnswerLabel)))}

    async def corpus_labels(self) -> dict[tuple[str, int], CorpusLabel]:
        return {
            (row.fixture, row.answer_index): row
            for row in (await self.session.scalars(select(CorpusLabel)))
        }

    async def latest_verdicts(self) -> dict[UUID, tuple[JudgeVerdict, JudgeRun]]:
        """Each answer's verdict from its most recent judging."""
        stmt = (
            select(JudgeVerdict, JudgeRun)
            .join(JudgeRun, JudgeRun.id == JudgeVerdict.judge_run_id)
            .order_by(JudgeRun.judged_at)
        )
        latest: dict[UUID, tuple[JudgeVerdict, JudgeRun]] = {}
        for verdict, judging in (await self.session.execute(stmt)).all():
            latest[verdict.answer_id] = (verdict, judging)
        return latest

    async def label_answer(
        self,
        answer_id: UUID,
        verdict: LabelVerdict,
        note: str | None,
        by: UUID,
        at: datetime,
    ) -> None:
        values = {"verdict": verdict, "note": note, "labelled_by": by, "labelled_at": at}
        stmt = (
            insert(AnswerLabel)
            .values(answer_id=answer_id, **values)
            .on_conflict_do_update(index_elements=["answer_id"], set_=values)
        )
        await self.session.execute(stmt)

    async def label_corpus(
        self,
        fixture: str,
        index: int,
        verdict: LabelVerdict,
        note: str | None,
        by: UUID,
        at: datetime,
    ) -> None:
        values = {"verdict": verdict, "note": note, "labelled_by": by, "labelled_at": at}
        stmt = (
            insert(CorpusLabel)
            .values(fixture=fixture, answer_index=index, **values)
            .on_conflict_do_update(index_elements=["fixture", "answer_index"], set_=values)
        )
        await self.session.execute(stmt)

    def add_judging(self, judging: JudgeRun, verdicts: list[JudgeVerdict]) -> None:
        self.session.add(judging)
        self.session.add_all(verdicts)

    async def runs_with_titles(self) -> list[tuple[SurveyRun, str]]:
        stmt = (
            select(SurveyRun, SurveyTemplate.title)
            .join(SurveyTemplate, SurveyTemplate.id == SurveyRun.template_id)
            .order_by(SurveyRun.started_at)
        )
        return [(run, title) for run, title in (await self.session.execute(stmt)).all()]

    async def all_answers(self) -> list[Answer]:
        return list((await self.session.scalars(select(Answer).order_by(Answer.answered_at))).all())

    async def turn_waits(self) -> list[tuple[UUID, int]]:
        """How long each traced turn took, by run: the respondent's wait for a reply."""
        stmt = select(LLMSpan.run_id, LLMSpan.duration_ms).where(
            LLMSpan.kind == SpanKind.turn, LLMSpan.run_id.is_not(None)
        )
        return [
            (run_id, duration)
            for run_id, duration in (await self.session.execute(stmt)).all()
            if run_id is not None
        ]
