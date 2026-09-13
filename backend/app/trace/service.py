"""What the lens pages read: traced runs, one run's spans, and totals across every run.

Admins only, asked here as well as at the route. Spans hold refusal reasons that can
quote a value a model proposed from a respondent's words, so the question is asked where
the data leaves the layer and not only at the door, which is also what
``check_access_consulted`` holds every service to.
"""

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access import is_admin
from app.config import get_settings
from app.errors import ForbiddenError, NotFoundError
from app.trace.models import LLMSpan
from app.trace.repository import SpanRepository
from app.trace.schemas import (
    AttemptRow,
    CorrelationCell,
    CorrelationMatrix,
    DecisionRow,
    LensStrip,
    SpanRead,
    TierStrip,
    TracedRun,
)
from app.trace.stats import MIN_SAMPLES, bootstrap_interval, spearman
from app.users.models import User

ADMINS_ONLY = "The lens is for administrators: traces can quote what respondents said."


def _money(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


@dataclass(frozen=True)
class _Placed:
    """A span with the run context the factor rows need: its survey, its turn."""

    span: LLMSpan
    survey_title: str
    turn: LLMSpan
    turn_number: int


def _place(rows: list[tuple[LLMSpan, str]]) -> dict[Any, _Placed]:
    """Walk each span up to its turn and number the turns within each run.

    Done here rather than in SQL because the tree is a parent chain of unknown depth (a
    retry nests under the ask it retries), and the scope is one survey's traces at most.
    A span whose chain does not reach a turn is left out: every span the engine writes
    has one, so this only drops spans some other writer made.
    """
    by_id = {span.id: span for span, _ in rows}
    title = {span.id: survey for span, survey in rows}
    turns_by_run: dict[Any, list[LLMSpan]] = {}
    for span, _ in rows:
        if span.kind.value == "turn":
            turns_by_run.setdefault(span.run_id, []).append(span)
    number = {
        turn.id: index
        for turns in turns_by_run.values()
        for index, turn in enumerate(sorted(turns, key=lambda t: t.started_at), start=1)
    }
    placed: dict[Any, _Placed] = {}
    for span, _ in rows:
        node: LLMSpan | None = span
        while node is not None and node.kind.value != "turn":
            node = by_id.get(node.parent_id) if node.parent_id is not None else None
        if node is not None:
            placed[span.id] = _Placed(span, title[span.id], node, number[node.id])
    return placed


def _maybe(value: int | None) -> float | None:
    return None if value is None else float(value)


def _flag(attrs: dict[str, Any], key: str) -> bool | None:
    """A recorded flag, or None when the span predates it. Unknown is not false."""
    value = attrs.get(key)
    return value if isinstance(value, bool) else None


def _whole(attrs: dict[str, Any], key: str) -> int | None:
    value = attrs.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _text(attrs: dict[str, Any], key: str) -> str | None:
    value = attrs.get(key)
    return value if isinstance(value, str) else None


class LensService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = SpanRepository(session)

    async def runs(self, viewer: User) -> list[TracedRun]:
        """Every traced run, newest first."""
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)
        return [
            TracedRun(
                run_id=row.run_id,
                template_id=row.template_id,
                survey_title=row.title,
                started_at=row.started_at,
                last_traced_at=row.last_traced_at,
                turns=row.turns,
                decisions=row.decisions,
                retries=row.retries,
                attempts=row.attempts,
                failed_attempts=row.failed_attempts,
                unmetered_attempts=row.unmetered_attempts,
                prompt_tokens=row.prompt_tokens,
                completion_tokens=row.completion_tokens,
                cached_tokens=row.cached_tokens,
                reasoning_tokens=row.reasoning_tokens,
                cost_usd=_money(row.cost_usd),
                turn_ms=row.turn_ms,
                first_token_ms_p50=row.first_token_ms_p50,
            )
            for row in await self.repo.run_totals()
        ]

    async def spans(self, run_id: UUID, viewer: User) -> list[SpanRead]:
        """One run's spans, oldest first, flat."""
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)
        spans = await self.repo.for_run(run_id)
        if not spans:
            raise NotFoundError(
                "This run has no trace. Turns are traced from 13 Sep 2026, and a withdrawn "
                "run takes its trace with it."
            )
        return [SpanRead.model_validate(span) for span in spans]

    async def strip(self, viewer: User) -> LensStrip:
        """Totals across every traced run, then one row per tier and model."""
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)
        overall = await self.repo.overall()
        return LensStrip(
            runs=overall.runs,
            turns=overall.turns,
            retries=overall.retries,
            turn_ms_p50=overall.turn_ms_p50,
            tiers=[
                TierStrip(
                    tier=row.tier,
                    model=row.model,
                    attempts=row.attempts,
                    failed_attempts=row.failed_attempts,
                    unmetered_attempts=row.unmetered_attempts,
                    prompt_tokens=row.prompt_tokens,
                    completion_tokens=row.completion_tokens,
                    cached_tokens=row.cached_tokens,
                    reasoning_tokens=row.reasoning_tokens,
                    cost_usd=_money(row.cost_usd),
                    latency_ms_p50=row.latency_ms_p50,
                    latency_ms_p95=row.latency_ms_p95,
                    first_token_ms_p50=row.first_token_ms_p50,
                    first_token_ms_p95=row.first_token_ms_p95,
                )
                for row in await self.repo.tier_totals()
            ],
        )

    async def attempts(
        self, viewer: User, survey_id: UUID | None, run_id: UUID | None
    ) -> list[AttemptRow]:
        """Every attempt in scope, oldest first, placed in its run and turn."""
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)
        placed = _place(await self.repo.in_scope(survey_id, run_id))
        by_id = {p.span.id: p.span for p in placed.values()}
        rows = []
        for p in placed.values():
            span = p.span
            if span.kind.value != "attempt":
                continue
            decision = by_id.get(span.parent_id) if span.parent_id is not None else None
            decision_attrs = decision.attrs if decision is not None else {}
            rows.append(
                AttemptRow(
                    id=span.id,
                    run_id=p.turn.run_id,
                    survey_title=p.survey_title,
                    started_at=span.started_at,
                    turn_number=p.turn_number,
                    question_index=_whole(p.turn.attrs, "question_index"),
                    retry=_flag(decision_attrs, "retry") is True,
                    transcript_messages=_whole(decision_attrs, "transcript_messages"),
                    tier=span.tier,
                    model=span.model,
                    status=span.status,
                    error=span.error,
                    duration_ms=span.duration_ms,
                    first_token_ms=span.first_token_ms,
                    prompt_tokens=span.prompt_tokens,
                    cached_tokens=span.cached_tokens,
                    completion_tokens=span.completion_tokens,
                    reasoning_tokens=span.reasoning_tokens,
                    cost_usd=_money(span.cost_usd),
                )
            )
        return rows

    async def decisions(
        self, viewer: User, survey_id: UUID | None, run_id: UUID | None
    ) -> list[DecisionRow]:
        """Every ask in scope, oldest first, with its check and its own attempts."""
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)
        placed = _place(await self.repo.in_scope(survey_id, run_id))
        children: dict[Any, list[LLMSpan]] = {}
        for p in placed.values():
            if p.span.parent_id is not None:
                children.setdefault(p.span.parent_id, []).append(p.span)
        rows = []
        for p in placed.values():
            span = p.span
            if span.kind.value != "decision":
                continue
            attrs = span.attrs
            under = children.get(span.id, [])
            attempts = [c for c in under if c.kind.value == "attempt"]
            checks = [c for c in under if c.kind.value == "validation"]
            check = checks[-1].attrs if checks else {}
            costs = [c.cost_usd for c in attempts if c.cost_usd is not None]
            offered = attrs.get("tools_offered")
            rows.append(
                DecisionRow(
                    id=span.id,
                    run_id=p.turn.run_id,
                    survey_title=p.survey_title,
                    started_at=span.started_at,
                    turn_number=p.turn_number,
                    question_index=_whole(p.turn.attrs, "question_index"),
                    retry=_flag(attrs, "retry") is True,
                    duration_ms=span.duration_ms,
                    error=span.error,
                    answer_type=_text(attrs, "answer_type"),
                    follow_up_policy=_text(attrs, "follow_up_policy"),
                    forced_probe=_flag(attrs, "forced_probe"),
                    probe_outstanding=_flag(attrs, "probe_outstanding"),
                    scripted_recorded=_flag(attrs, "scripted_recorded"),
                    recorded_this_turn=_flag(attrs, "recorded_this_turn"),
                    follow_ups_used=_whole(attrs, "follow_ups_used"),
                    replies_used=_whole(attrs, "replies_used"),
                    transcript_messages=_whole(attrs, "transcript_messages"),
                    tools_offered=([str(t) for t in offered] if isinstance(offered, list) else []),
                    resolved_to=_text(attrs, "resolved_to"),
                    picked=_text(check, "tool"),
                    outcome=_text(check, "outcome"),
                    reason=_text(check, "reason"),
                    attempts=len(attempts),
                    failed_attempts=sum(1 for c in attempts if c.error is not None),
                    attempt_ms=sum(c.duration_ms for c in attempts),
                    # Unknown only when no attempt under it was priced; otherwise the sum of
                    # the priced ones, as the run totals do.
                    cost_usd=_money(sum(costs, Decimal(0))) if costs else None,
                )
            )
        return rows

    async def correlations(
        self, viewer: User, survey_id: UUID | None, run_id: UUID | None
    ) -> CorrelationMatrix:
        """Each factor of a call against each outcome, ranked, with a bootstrap interval.

        Correlation over real traffic, not cause: a prompt that grew because the transcript
        did also sits later in the run, and this cannot tell the two apart.
        """
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)
        rows = await self.attempts(viewer, survey_id, run_id)

        def writing(row: AttemptRow) -> float | None:
            if row.first_token_ms is None:
                return None
            return float(row.duration_ms - row.first_token_ms)

        factors: dict[str, Callable[[AttemptRow], float | None]] = {
            "tokens_in": lambda r: _maybe(r.prompt_tokens),
            "cached_tokens": lambda r: _maybe(r.cached_tokens),
            "tokens_out": lambda r: _maybe(r.completion_tokens),
            "transcript_messages": lambda r: _maybe(r.transcript_messages),
            "turn_number": lambda r: float(r.turn_number),
            "retry": lambda r: 1.0 if r.retry else 0.0,
        }
        outcomes: dict[str, Callable[[AttemptRow], float | None]] = {
            "first_token_ms": lambda r: _maybe(r.first_token_ms),
            "writing_ms": writing,
            "duration_ms": lambda r: float(r.duration_ms),
            "cost_usd": lambda r: r.cost_usd,
        }
        cells = []
        for factor, read_factor in factors.items():
            for outcome, read_outcome in outcomes.items():
                pairs = [
                    (x, y)
                    for x, y in ((read_factor(r), read_outcome(r)) for r in rows)
                    if x is not None and y is not None
                ]
                xs = [x for x, _ in pairs]
                ys = [y for _, y in pairs]
                rho = spearman(xs, ys)
                too_few = len(pairs) < MIN_SAMPLES
                interval = None if too_few or rho is None else bootstrap_interval(xs, ys)
                cells.append(
                    CorrelationCell(
                        factor=factor,
                        outcome=outcome,
                        n=len(pairs),
                        rho=rho,
                        ci_low=interval[0] if interval else None,
                        ci_high=interval[1] if interval else None,
                        too_few=too_few,
                        no_variation=len(pairs) >= 2 and rho is None,
                    )
                )
        return CorrelationMatrix(
            factors=list(factors),
            outcomes=list(outcomes),
            min_samples=MIN_SAMPLES,
            cells=cells,
        )
