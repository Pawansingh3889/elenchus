"""Every query the evaluation lens makes."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.evaluation.enums import LabelVerdict
from app.evaluation.models import AnswerLabel, CorpusLabel, EvalRun, JudgeRun, JudgeVerdict
from app.interp.models import InterpAnalysis
from app.runs.enums import AnswerKind
from app.runs.models import Answer, RunMessage, SurveyRun
from app.templates.models import SurveyQuestion, SurveyTemplate
from app.trace.enums import SpanKind
from app.trace.models import LLMSpan
from app.users.models import User


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
            .on_conflict_do_update(
                index_elements=["workspace_id", "fixture", "answer_index"], set_=values
            )
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

    async def evaluation_accounts(
        self, author: tuple[str, str], respondent: tuple[str, str]
    ) -> tuple[User, User]:
        """The two accounts evaluation runs act as, made on first use.

        No job on either, so they sit in no audience and no reach count. Inserted with
        conflicts skipped, because two batches starting at once would otherwise race to
        create the same address.
        """
        workspace_id = await self.session.scalar(select(func.current_setting("app.workspace_id")))
        if not workspace_id:
            raise ValueError("Evaluation accounts require a workspace.")
        author = (f"{workspace_id}.{author[0]}", author[1])
        respondent = (f"{workspace_id}.{respondent[0]}", respondent[1])
        for email, name in (author, respondent):
            await self.session.execute(
                insert(User)
                .values(id=uuid4(), email=email, display_name=name)
                .on_conflict_do_nothing(index_elements=["email"])
            )
        stmt = select(User).where(User.email.in_([author[0], respondent[0]]))
        found = {user.email: user for user in (await self.session.scalars(stmt))}
        return found[author[0]], found[respondent[0]]

    def add_eval_runs(self, rows: list[EvalRun]) -> None:
        self.session.add_all(rows)

    async def eval_run(self, eval_run_id: UUID) -> EvalRun | None:
        return await self.session.get(EvalRun, eval_run_id, populate_existing=True)

    async def eval_runs_in_batch(self, batch_id: UUID) -> list[EvalRun]:
        stmt = select(EvalRun).where(EvalRun.batch_id == batch_id).order_by(EvalRun.position)
        return list((await self.session.scalars(stmt)).all())

    async def eval_runs(self, limit: int) -> list[EvalRun]:
        # Fresh from the database: rows are moved on by the background runner, in its
        # own sessions, while this session may still hold the queued copies it created.
        stmt = (
            select(EvalRun)
            .order_by(EvalRun.queued_at.desc(), EvalRun.position)
            .limit(limit)
            .execution_options(populate_existing=True)
        )
        return list((await self.session.scalars(stmt)).all())

    async def all_eval_runs(self) -> list[EvalRun]:
        """Every evaluation run, oldest first, fresh from the database."""
        stmt = (
            select(EvalRun)
            .order_by(EvalRun.queued_at, EvalRun.position)
            .execution_options(populate_existing=True)
        )
        return list((await self.session.scalars(stmt)).all())

    async def readings(
        self,
    ) -> list[tuple[dict[str, Any], LLMSpan, dict[str, Any] | None, dict[str, Any] | None]]:
        """Each stored Qwen reading with the hosted attempt it read, the attrs of the
        decision that attempt served, and the engine's check of that decision.

        The decision or its check is None when the trace holds none: a failed attempt's
        decision may have been retried, and a reading of it has no check to compare.
        """
        stmt = select(InterpAnalysis.result, LLMSpan).join(
            LLMSpan, LLMSpan.id == InterpAnalysis.span_id
        )
        rows = [(result, attempt) for result, attempt in (await self.session.execute(stmt)).all()]
        parents = [attempt.parent_id for _, attempt in rows if attempt.parent_id is not None]
        decisions: dict[UUID, dict[str, Any]] = {}
        checks: dict[UUID, dict[str, Any]] = {}
        if parents:
            for span in await self.session.scalars(select(LLMSpan).where(LLMSpan.id.in_(parents))):
                decisions[span.id] = span.attrs
            validations = select(LLMSpan.parent_id, LLMSpan.attrs).where(
                LLMSpan.parent_id.in_(parents), LLMSpan.kind == SpanKind.validation
            )
            for parent, attrs in (await self.session.execute(validations)).all():
                checks[parent] = attrs
        return [
            (
                result,
                attempt,
                None if attempt.parent_id is None else decisions.get(attempt.parent_id),
                None if attempt.parent_id is None else checks.get(attempt.parent_id),
            )
            for result, attempt in rows
        ]

    async def scripted_labels(self) -> dict[tuple[UUID, str], LabelVerdict]:
        """People's labels on scripted answers, by run and question."""
        stmt = (
            select(Answer.run_id, Answer.question_id, AnswerLabel.verdict)
            .join(AnswerLabel, AnswerLabel.answer_id == Answer.id)
            .where(Answer.kind == AnswerKind.scripted)
        )
        return {
            (run_id, str(question_id)): verdict
            for run_id, question_id, verdict in (await self.session.execute(stmt)).all()
        }
