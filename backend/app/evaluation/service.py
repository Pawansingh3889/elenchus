"""The labelling queue, the faithfulness report, and judging a run on request."""

import time
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.access import is_admin
from app.config import get_settings
from app.errors import ForbiddenError, NotFoundError, ValidationError
from app.evaluation.corpus import CorpusAnswer, load_corpus
from app.evaluation.enums import LabelVerdict
from app.evaluation.judge import JUDGE_PROMPT_VERSION, ask_judge
from app.evaluation.models import JudgeRun, JudgeVerdict
from app.evaluation.repository import EvaluationRepository
from app.evaluation.schemas import (
    EvalItem,
    FaithfulnessReport,
    FaithfulnessSlice,
    JudgeRunRead,
    LabelRequest,
    Rate,
    Source,
)
from app.evaluation.stats import MIN_LABELLED, wilson
from app.llm import ledger
from app.llm.client import LLMProtocol
from app.llm.factory import get_llm
from app.runs.enums import MessageRole
from app.users.models import User

ADMINS_ONLY = "The evaluation lens is for administrators: it shows what respondents typed."
CORPUS_PREFIX = "corpus:"
ANSWER_PREFIX = "answer:"


def _rate(numerator: int, denominator: int) -> Rate:
    interval = wilson(numerator, denominator)
    return Rate(
        numerator=numerator,
        denominator=denominator,
        value=None if denominator == 0 else numerator / denominator,
        low=None if interval is None else interval[0],
        high=None if interval is None else interval[1],
        too_few=denominator < MIN_LABELLED,
    )


def _slice(name: str, items: list[EvalItem]) -> FaithfulnessSlice:
    supported = [i for i in items if i.label is LabelVerdict.supported]
    invented = [i for i in items if i.label is LabelVerdict.invented]
    decisive = supported + invented
    judged = [i for i in decisive if i.judge_supported is not None]
    flagged = [i for i in judged if i.judge_supported is False]
    caught = [i for i in flagged if i.label is LabelVerdict.invented]
    invented_judged = [i for i in judged if i.label is LabelVerdict.invented]
    supported_judged = [i for i in judged if i.label is LabelVerdict.supported]
    return FaithfulnessSlice(
        name=name,
        items=len(items),
        labelled=sum(1 for i in items if i.label is not None),
        supported=len(supported),
        invented=len(invented),
        unsure=sum(1 for i in items if i.label is LabelVerdict.unsure),
        invention_rate=_rate(len(invented), len(decisive)),
        judged_and_labelled=len(judged),
        judge_precision=_rate(len(caught), len(flagged)),
        judge_recall=_rate(len(caught), len(invented_judged)),
        judge_false_alarms=_rate(
            sum(1 for i in supported_judged if i.judge_supported is False), len(supported_judged)
        ),
    )


def _slices(items: list[EvalItem], key: Callable[[EvalItem], str]) -> list[FaithfulnessSlice]:
    groups: dict[str, list[EvalItem]] = {}
    for item in items:
        groups.setdefault(key(item), []).append(item)
    return [_slice(name, group) for name, group in sorted(groups.items())]


class EvaluationService:
    def __init__(
        self,
        session: AsyncSession,
        llm: LLMProtocol | None = None,
        corpus_dir: Path | None = None,
    ) -> None:
        self.session = session
        self.repo = EvaluationRepository(session)
        self._llm = llm
        self._corpus_dir = corpus_dir

    @property
    def llm(self) -> LLMProtocol:
        if self._llm is None:
            self._llm = get_llm()
        return self._llm

    def _require_admin(self, viewer: User) -> None:
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)

    async def items(self, viewer: User, source: Source, unlabelled_only: bool) -> list[EvalItem]:
        """The labelling queue for one source, oldest first."""
        self._require_admin(viewer)
        found = await (self._corpus_items() if source == "corpus" else self._run_items())
        return [item for item in found if not unlabelled_only or item.label is None]

    async def label(self, viewer: User, key: str, request: LabelRequest) -> EvalItem:
        """Set, or replace, a person's label on one answer."""
        self._require_admin(viewer)
        at = datetime.now(UTC)
        if key.startswith(CORPUS_PREFIX):
            fixture, _, position = key.removeprefix(CORPUS_PREFIX).rpartition(":")
            if not position.isdigit() or not any(
                a.fixture == fixture and a.index == int(position) for a in self._corpus()
            ):
                raise NotFoundError(f"No corpus answer {key!r}.")
            await self.repo.label_corpus(
                fixture, int(position), request.verdict, request.note, viewer.id, at
            )
            await self.session.commit()
            return next(i for i in await self._corpus_items() if i.key == key)
        if key.startswith(ANSWER_PREFIX):
            try:
                answer_id = UUID(key.removeprefix(ANSWER_PREFIX))
            except ValueError as exc:
                raise NotFoundError(f"No answer {key!r}.") from exc
            if not await self.repo.answers(answer_id):
                raise NotFoundError(f"No answer {key!r}.")
            await self.repo.label_answer(answer_id, request.verdict, request.note, viewer.id, at)
            await self.session.commit()
            (item,) = await self._run_items(answer_id)
            return item
        raise NotFoundError(f"{key!r} names neither a corpus answer nor a database answer.")

    async def faithfulness(self, viewer: User) -> FaithfulnessReport:
        """Invention rate and the judge's agreement with people, with intervals."""
        self._require_admin(viewer)
        items = [*(await self._corpus_items()), *(await self._run_items())]
        return FaithfulnessReport(
            min_labelled=MIN_LABELLED,
            overall=_slice("all", items),
            by_source=_slices(items, lambda item: item.source),
            by_answer_type=_slices(items, lambda item: item.answer_type),
            by_model=_slices(items, lambda item: item.model or "not recorded"),
        )

    async def judge_run(self, viewer: User, run_id: UUID) -> JudgeRunRead:
        """Ask the judge about every answer in one run: one model call, priced and kept."""
        self._require_admin(viewer)
        run = await self.repo.run(run_id)
        if run is None:
            raise NotFoundError("No run with that id.")
        answers = await self.repo.answers_for_run(run_id)
        if not answers:
            raise ValidationError("This run has no recorded answers to judge.")
        said = [m.content for m in await self.repo.messages([run_id]) if m.role is MessageRole.user]
        recorded = [
            {"index": index, "question": answer.question_text, "recorded_answer": answer.value}
            for index, answer in enumerate(answers)
        ]
        started = time.monotonic()
        with ledger.measuring(run_id) as spend, ledger.using_prompt(JUDGE_PROMPT_VERSION):
            # Resolved against the day the conversation happened, which is the day a
            # respondent's "last Monday" meant.
            verdicts = await ask_judge(
                self.llm, said=said, recorded=recorded, today=run.started_at.date()
            )
        judging = JudgeRun(
            id=uuid4(),
            run_id=run_id,
            prompt_version=JUDGE_PROMPT_VERSION,
            model=spend.last_model,
            tier=spend.last_tier,
            answers=len(answers),
            flagged=sum(1 for verdict in verdicts if not verdict.supported),
            cost_usd=Decimal(str(round(spend.cost_usd, ledger.COST_PLACES))),
            unmetered_calls=spend.unmetered_calls,
            duration_ms=int((time.monotonic() - started) * 1000),
            judged_at=datetime.now(UTC),
        )
        self.repo.add_judging(
            judging,
            [
                JudgeVerdict(
                    judge_run_id=judging.id,
                    answer_id=answers[verdict.index].id,
                    supported=verdict.supported,
                    why=verdict.why,
                )
                for verdict in verdicts
            ],
        )
        await self.session.commit()
        return JudgeRunRead.model_validate(judging, from_attributes=True)

    def _corpus(self) -> list[CorpusAnswer]:
        return load_corpus(self._corpus_dir)

    async def _corpus_items(self) -> list[EvalItem]:
        labels = await self.repo.corpus_labels()
        items = []
        for answer in self._corpus():
            label = labels.get((answer.fixture, answer.index))
            items.append(
                EvalItem(
                    key=f"{CORPUS_PREFIX}{answer.fixture}:{answer.index}",
                    source="corpus",
                    origin=answer.fixture,
                    run_id=None,
                    model=answer.model,
                    when=answer.captured_at,
                    question_text=answer.question_text,
                    answer_type=answer.answer_type,
                    options=answer.options,
                    kind=answer.kind,
                    value=answer.value,
                    said=answer.said,
                    judge_supported=answer.judge_supported,
                    judge_why=answer.judge_why,
                    judge_prompt=None if answer.judge_supported is None else "live check",
                    marked_invented=answer.marked_invented,
                    label=None if label is None else label.verdict,
                    note=None if label is None else label.note,
                    labelled_at=None if label is None else label.labelled_at,
                )
            )
        return items

    async def _run_items(self, answer_id: UUID | None = None) -> list[EvalItem]:
        rows = await self.repo.answers(answer_id)
        messages = await self.repo.messages(sorted({answer.run_id for answer, _, _ in rows}))
        labels = await self.repo.answer_labels()
        verdicts = await self.repo.latest_verdicts()
        items = []
        for answer, question, title in rows:
            own = [m for m in messages if m.run_id == answer.run_id]
            said = [
                m.content
                for m in own
                if m.role is MessageRole.user and m.created_at <= answer.answered_at
            ]
            # The model whose reply followed the answer is the one that recorded it.
            reply = next(
                (
                    m
                    for m in own
                    if m.role is MessageRole.assistant and m.created_at >= answer.answered_at
                ),
                None,
            )
            label = labels.get(answer.id)
            verdict = verdicts.get(answer.id)
            items.append(
                EvalItem(
                    key=f"{ANSWER_PREFIX}{answer.id}",
                    source="runs",
                    origin=title,
                    run_id=answer.run_id,
                    model=None if reply is None else reply.model,
                    when=answer.answered_at.isoformat(),
                    question_text=answer.question_text,
                    answer_type="unknown" if question is None else question.answer_type.value,
                    options=[] if question is None else list(question.options or []),
                    kind=answer.kind.value,
                    value=answer.value,
                    said=said,
                    judge_supported=None if verdict is None else verdict[0].supported,
                    judge_why=None if verdict is None else verdict[0].why,
                    judge_prompt=None if verdict is None else verdict[1].prompt_version,
                    marked_invented=False,
                    label=None if label is None else label.verdict,
                    note=None if label is None else label.note,
                    labelled_at=None if label is None else label.labelled_at,
                )
            )
        return items
