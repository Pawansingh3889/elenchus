"""Span writes and reads. The only module that queries llm_spans."""

from typing import Any
from uuid import UUID

from sqlalchemy import ColumnElement, Row, delete, distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.runs.models import SurveyRun
from app.templates.models import SurveyTemplate
from app.trace.enums import SpanKind
from app.trace.models import LLMRequest, LLMSpan


def _unmetered() -> ColumnElement[bool]:
    """An attempt whose tokens or cost the provider never reported.

    The same rule the ledger's ``Spend.unmetered_calls`` counts by, so the lens and the
    run rollup cannot disagree about which calls were measured.
    """
    return or_(
        LLMSpan.cost_usd.is_(None),
        LLMSpan.prompt_tokens.is_(None),
        LLMSpan.completion_tokens.is_(None),
    )


def _token_sums() -> list[Any]:
    return [
        func.coalesce(func.sum(LLMSpan.prompt_tokens), 0).label("prompt_tokens"),
        func.coalesce(func.sum(LLMSpan.completion_tokens), 0).label("completion_tokens"),
        func.sum(LLMSpan.cached_tokens).label("cached_tokens"),
        func.sum(LLMSpan.reasoning_tokens).label("reasoning_tokens"),
        func.count()
        .filter(LLMSpan.kind == SpanKind.attempt, LLMSpan.cached_tokens.is_(None))
        .label("unreported_cached_attempts"),
        func.count()
        .filter(LLMSpan.kind == SpanKind.attempt, LLMSpan.reasoning_tokens.is_(None))
        .label("unreported_reasoning_attempts"),
        func.sum(LLMSpan.cost_usd).label("cost_usd"),
    ]


class SpanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_all(self, spans: list[LLMSpan]) -> None:
        self.session.add_all(spans)

    def add_requests(self, requests: list[LLMRequest]) -> None:
        self.session.add_all(requests)

    async def request_for(self, span_id: UUID) -> LLMRequest | None:
        return await self.session.get(LLMRequest, span_id)

    async def for_run(self, run_id: UUID) -> list[LLMSpan]:
        stmt = select(LLMSpan).where(LLMSpan.run_id == run_id).order_by(LLMSpan.started_at)
        return list((await self.session.scalars(stmt)).all())

    async def delete_for_run(self, run_id: UUID) -> None:
        """The run's spans and captured requests. Explicit, because run_id is not a foreign
        key on either (see the models docstring)."""
        await self.session.execute(delete(LLMRequest).where(LLMRequest.run_id == run_id))
        await self.session.execute(delete(LLMSpan).where(LLMSpan.run_id == run_id))

    async def run_totals(self) -> list[Row[Any]]:
        """One row per traced run, newest trace first.

        Aggregated in the database with FILTER, so every figure is a sum over the spans
        it describes and a page never re-derives one from a sample. Joined on the run id
        without a foreign key behind it, which is safe because withdrawal deletes spans
        with the run.
        """
        attempt = LLMSpan.kind == SpanKind.attempt
        stmt = (
            select(
                LLMSpan.run_id,
                SurveyRun.template_id,
                SurveyTemplate.title,
                SurveyRun.started_at,
                func.max(LLMSpan.started_at).label("last_traced_at"),
                func.count().filter(LLMSpan.kind == SpanKind.turn).label("turns"),
                func.count().filter(LLMSpan.kind == SpanKind.decision).label("decisions"),
                func.count()
                .filter(LLMSpan.kind == SpanKind.decision, LLMSpan.attrs["retry"].as_boolean())
                .label("retries"),
                func.count().filter(attempt).label("attempts"),
                func.count().filter(attempt, LLMSpan.error.is_not(None)).label("failed_attempts"),
                func.count().filter(attempt, _unmetered()).label("unmetered_attempts"),
                *_token_sums(),
                func.coalesce(
                    func.sum(LLMSpan.duration_ms).filter(LLMSpan.kind == SpanKind.turn), 0
                ).label("turn_ms"),
                # Only attempts carry a first-token time, and the percentile skips nulls.
                func.percentile_cont(0.5)
                .within_group(LLMSpan.first_token_ms)
                .label("first_token_ms_p50"),
            )
            .join(SurveyRun, SurveyRun.id == LLMSpan.run_id)
            .join(SurveyTemplate, SurveyTemplate.id == SurveyRun.template_id)
            .group_by(
                LLMSpan.run_id, SurveyRun.template_id, SurveyTemplate.title, SurveyRun.started_at
            )
            .order_by(func.max(LLMSpan.started_at).desc())
        )
        return list((await self.session.execute(stmt)).all())

    async def in_scope(
        self, survey_id: UUID | None, run_id: UUID | None
    ) -> list[tuple[LLMSpan, str]]:
        """Every span of the traced runs in scope, oldest first, with its survey's title.

        Rows rather than aggregates, because the factor pages chart distributions and
        link each point back to its run. The service places each span in its run and turn.
        """
        stmt = (
            select(LLMSpan, SurveyTemplate.title)
            .join(SurveyRun, SurveyRun.id == LLMSpan.run_id)
            .join(SurveyTemplate, SurveyTemplate.id == SurveyRun.template_id)
            .order_by(LLMSpan.started_at)
        )
        if survey_id is not None:
            stmt = stmt.where(SurveyRun.template_id == survey_id)
        if run_id is not None:
            stmt = stmt.where(LLMSpan.run_id == run_id)
        return [(span, title) for span, title in (await self.session.execute(stmt)).all()]

    async def tier_totals(self) -> list[Row[Any]]:
        """Every attempt, grouped by the tier and model that served it."""
        stmt = (
            select(
                LLMSpan.tier,
                LLMSpan.model,
                func.count().label("attempts"),
                func.count().filter(LLMSpan.error.is_not(None)).label("failed_attempts"),
                func.count().filter(_unmetered()).label("unmetered_attempts"),
                *_token_sums(),
                func.percentile_cont(0.5).within_group(LLMSpan.duration_ms).label("latency_ms_p50"),
                func.percentile_cont(0.95)
                .within_group(LLMSpan.duration_ms)
                .label("latency_ms_p95"),
                func.percentile_cont(0.5)
                .within_group(LLMSpan.first_token_ms)
                .label("first_token_ms_p50"),
                func.percentile_cont(0.95)
                .within_group(LLMSpan.first_token_ms)
                .label("first_token_ms_p95"),
            )
            .where(LLMSpan.kind == SpanKind.attempt)
            .group_by(LLMSpan.tier, LLMSpan.model)
            .order_by(LLMSpan.tier, LLMSpan.model)
        )
        return list((await self.session.execute(stmt)).all())

    async def overall(self) -> Row[Any]:
        """Runs, turns, retries and the median turn across every trace."""
        turn_p50 = (
            select(func.percentile_cont(0.5).within_group(LLMSpan.duration_ms))
            .where(LLMSpan.kind == SpanKind.turn)
            .scalar_subquery()
        )
        stmt = select(
            func.count(distinct(LLMSpan.run_id)).label("runs"),
            func.count().filter(LLMSpan.kind == SpanKind.turn).label("turns"),
            func.count()
            .filter(LLMSpan.kind == SpanKind.decision, LLMSpan.attrs["retry"].as_boolean())
            .label("retries"),
            turn_p50.label("turn_ms_p50"),
        )
        return (await self.session.execute(stmt)).one()
