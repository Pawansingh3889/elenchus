"""The labelling queue, the faithfulness report, and judging a run on request."""

import re
import time
from collections import Counter
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.access import is_admin
from app.conduct.engine import PROMPT_VERSION
from app.config import get_settings
from app.db.session import SessionFactory
from app.errors import ForbiddenError, NotFoundError, ValidationError
from app.evaluation import runner
from app.evaluation.corpus import CorpusAnswer, load_corpus
from app.evaluation.enums import EvalRunStatus, LabelVerdict
from app.evaluation.judge import JUDGE_PROMPT_VERSION, ask_judge
from app.evaluation.models import EvalRun, JudgeRun, JudgeVerdict
from app.evaluation.repository import EvaluationRepository
from app.evaluation.scenarios import SCENARIOS, Scenario, max_turns
from app.evaluation.schemas import (
    CheckRead,
    EvalItem,
    EvalOptions,
    EvalRunRead,
    EvalStartRequest,
    FaithfulnessReport,
    FaithfulnessSlice,
    JudgeRunRead,
    LabelRequest,
    Median,
    QualityReport,
    QualitySlice,
    Rate,
    ScenarioRead,
    Source,
    TierRead,
)
from app.evaluation.stats import MIN_LABELLED, median, wilson
from app.llm import ledger
from app.llm.client import LLMError, LLMProtocol
from app.llm.factory import enabled_tiers, get_llm, get_llm_for_tier
from app.llm.prompts import PROMPTS_DIR, PromptNotFoundError
from app.prompts.repository import PromptRepository
from app.prompts.service import PromptResolver
from app.runs.enums import AnswerKind, MessageRole, RunStatus
from app.runs.models import Answer, RunMessage, SurveyRun
from app.users.models import User

ADMINS_ONLY = "The evaluation lens is for administrators: it shows what respondents typed."
# A running scenario not heard from for this long has most likely lost its process.
STALE_AFTER_SECONDS = 15 * 60
EVAL_RUNS_SHOWN = 200
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


WORD = re.compile(r"[a-z0-9']+")


def _words(text: str) -> set[str]:
    return set(WORD.findall(text.lower()))


def _measured(values: list[float]) -> Median:
    return Median(value=median(values), n=len(values))


def _most_common(values: list[str | None]) -> str:
    present = [value for value in values if value]
    return Counter(present).most_common(1)[0][0] if present else "not recorded"


@dataclass
class _Conversation:
    run: SurveyRun
    title: str
    answers: list[Answer]
    said: list[RunMessage]
    replies: list[RunMessage]
    waits: list[int] = field(default_factory=list)

    @property
    def model(self) -> str:
        return _most_common([reply.model for reply in self.replies])

    @property
    def prompt(self) -> str:
        return _most_common([reply.prompt_version for reply in self.replies])

    def said_before(self, answer: Answer) -> RunMessage | None:
        """The respondent's latest message at or before this answer was recorded."""
        before = [m for m in self.said if m.created_at <= answer.answered_at]
        return before[-1] if before else None

    def follow_up_novelty(self) -> list[float]:
        shares = []
        for answer in self.answers:
            if answer.kind is not AnswerKind.follow_up:
                continue
            first = next(
                (
                    a
                    for a in self.answers
                    if a.kind is AnswerKind.scripted and a.question_id == answer.question_id
                ),
                None,
            )
            probe_reply = self.said_before(answer)
            first_reply = None if first is None else self.said_before(first)
            if probe_reply is None or first_reply is None or probe_reply.id == first_reply.id:
                continue
            words = _words(probe_reply.content)
            if words:
                shares.append(len(words - _words(first_reply.content)) / len(words))
        return shares


def _quality_slice(name: str, conversations: list[_Conversation]) -> QualitySlice:
    answers = [a for c in conversations for a in c.answers]
    completed = [c for c in conversations if c.run.status is RunStatus.completed]
    total_cost = sum(float(c.run.llm_cost_usd) for c in conversations)
    return QualitySlice(
        name=name,
        runs=len(conversations),
        completion=_rate(len(completed), len(conversations)),
        answers=len(answers),
        declined=_rate(sum(1 for a in answers if "unanswerable" in a.value), len(answers)),
        turns_per_answer=_measured(
            [len(c.said) / len(c.answers) for c in conversations if c.answers]
        ),
        respondent_chars=_measured(
            [float(sum(len(m.content) for m in c.said)) for c in conversations]
        ),
        minutes_to_complete=_measured(
            [
                (c.run.completed_at - c.run.started_at).total_seconds() / 60
                for c in completed
                if c.run.completed_at is not None
            ]
        ),
        wait_ms_per_turn=_measured([float(w) for c in conversations for w in c.waits]),
        follow_ups_asked=sum(sum(c.run.probes_asked.values()) for c in conversations),
        follow_up_answers=sum(1 for a in answers if a.kind is AnswerKind.follow_up),
        follow_up_new_words=_measured([s for c in conversations for s in c.follow_up_novelty()]),
        cost_per_completed_run=_measured([float(c.run.llm_cost_usd) for c in completed]),
        cost_per_answer=None if not answers else total_cost / len(answers),
        unmetered_calls=sum(c.run.llm_unmetered_calls for c in conversations),
    )


def _quality_slices(
    conversations: list[_Conversation], key: Callable[[_Conversation], str]
) -> list[QualitySlice]:
    groups: dict[str, list[_Conversation]] = {}
    for conversation in conversations:
        groups.setdefault(key(conversation), []).append(conversation)
    return [_quality_slice(name, group) for name, group in sorted(groups.items())]


class EvaluationService:
    def __init__(
        self,
        session: AsyncSession,
        llm: LLMProtocol | None = None,
        corpus_dir: Path | None = None,
        *,
        sessions: async_sessionmaker[AsyncSession] | None = None,
        make_llm: Callable[[int], LLMProtocol] | None = None,
        catalogue: dict[str, Scenario] | None = None,
        launch: Callable[[Coroutine[Any, Any, None]], None] | None = None,
    ) -> None:
        self.session = session
        self.repo = EvaluationRepository(session)
        self._llm = llm
        self._corpus_dir = corpus_dir
        # Evaluation runs outlive the request, so they get their own sessions, a model per
        # pinned tier, and a way to be started in the background. Tests swap each one.
        self._sessions = SessionFactory if sessions is None else sessions
        self._make_llm: Callable[[int], LLMProtocol] = (
            get_llm_for_tier if make_llm is None else make_llm
        )
        self._catalogue = SCENARIOS if catalogue is None else catalogue
        self._launch = runner.launch if launch is None else launch

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

    async def quality(self, viewer: User) -> QualityReport:
        """How conversations went: completion, effort, waiting, probing and cost, measured."""
        self._require_admin(viewer)
        runs = await self.repo.runs_with_titles()
        answers = await self.repo.all_answers()
        messages = await self.repo.messages([run.id for run, _ in runs])
        waits = await self.repo.turn_waits()
        conversations = []
        for run, title in runs:
            own = [m for m in messages if m.run_id == run.id]
            said = [m for m in own if m.role is MessageRole.user]
            if not said:
                continue
            conversations.append(
                _Conversation(
                    run=run,
                    title=title,
                    answers=[a for a in answers if a.run_id == run.id],
                    said=said,
                    replies=[m for m in own if m.role is MessageRole.assistant],
                    waits=[duration for run_id, duration in waits if run_id == run.id],
                )
            )
        return QualityReport(
            runs_without_conversation=len(runs) - len(conversations),
            overall=_quality_slice("all", conversations),
            by_survey=_quality_slices(conversations, lambda c: c.title),
            by_model=_quality_slices(conversations, lambda c: c.model),
            by_prompt=_quality_slices(conversations, lambda c: c.prompt),
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

    async def eval_options(self, viewer: User) -> EvalOptions:
        """What an evaluation batch can be made of on this deployment."""
        self._require_admin(viewer)
        prompts = PromptRepository(self.session)
        files = {path.stem for path in PROMPTS_DIR.glob("conduct_v*.md")}
        saved = {version.name for version, _ in await prompts.versions("conduct")}
        return EvalOptions(
            scenarios=[
                ScenarioRead(
                    key=s.key,
                    title=s.title,
                    questions=len(s.questions),
                    max_turns=max_turns(s),
                )
                for s in self._catalogue.values()
            ],
            tiers=[TierRead(tier=tier, model=model) for tier, model in enabled_tiers()],
            prompt_versions=sorted(files | saved, key=lambda name: (len(name), name)),
            active_prompt=await prompts.active_name("conduct") or PROMPT_VERSION,
        )

    async def start_eval(self, viewer: User, request: EvalStartRequest) -> list[EvalRunRead]:
        """Queue a batch and start it in the background. Every refusal happens here, first."""
        self._require_admin(viewer)
        unknown = [key for key in request.scenarios if key not in self._catalogue]
        if unknown:
            raise ValidationError(f"No such scenario: {', '.join(unknown)}.")
        if len(set(request.scenarios)) != len(request.scenarios):
            raise ValidationError("A batch runs each scenario once.")
        try:
            self._make_llm(request.tier)
        except LLMError as exc:
            raise ValidationError(str(exc)) from exc
        prompt = request.prompt_version or (
            await PromptRepository(self.session).active_name("conduct") or PROMPT_VERSION
        )
        try:
            await PromptResolver(self.session).text(prompt)
        except PromptNotFoundError as exc:
            raise ValidationError(f"No conduct prompt version {prompt!r}.") from exc

        batch_id = uuid4()
        rows = runner.queued_rows(
            batch_id,
            request.scenarios,
            tier=request.tier,
            prompt_version=prompt,
            cap_usd=Decimal(str(request.cap_usd)),
            created_by=viewer.id,
            at=datetime.now(UTC),
        )
        self.repo.add_eval_runs(rows)
        await self.session.commit()
        self._launch(runner.run_batch(self._sessions, batch_id, self._make_llm, self._catalogue))
        return [self._eval_read(row) for row in rows]

    async def eval_runs(self, viewer: User) -> list[EvalRunRead]:
        """Recent evaluation runs, newest batch first."""
        self._require_admin(viewer)
        return [self._eval_read(row) for row in await self.repo.eval_runs(EVAL_RUNS_SHOWN)]

    def _eval_read(self, row: EvalRun) -> EvalRunRead:
        stale = (
            row.status is EvalRunStatus.running
            and row.heartbeat_at is not None
            and (datetime.now(UTC) - row.heartbeat_at).total_seconds() > STALE_AFTER_SECONDS
        )
        return EvalRunRead(
            id=row.id,
            batch_id=row.batch_id,
            position=row.position,
            scenario=row.scenario,
            tier=row.tier,
            model=row.model,
            prompt_version=row.prompt_version,
            status=row.status,
            cap_usd=float(row.cap_usd),
            run_id=row.run_id,
            template_id=row.template_id,
            turns=row.turns or 0,
            answers=row.answers or 0,
            hard_failures=row.hard_failures or 0,
            soft_failures=row.soft_failures or 0,
            checks=[CheckRead(**check) for check in row.checks],
            cost_usd=float(row.cost_usd or 0),
            unmetered_calls=row.unmetered_calls or 0,
            duration_ms=row.duration_ms or 0,
            error=row.error,
            queued_at=row.queued_at,
            started_at=row.started_at,
            finished_at=row.finished_at,
            heartbeat_at=row.heartbeat_at,
            stale=stale,
        )
