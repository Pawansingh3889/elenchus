"""Every query the interpretability lens makes: captured calls, their checks, analyses."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Row, delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.interp.models import InterpAnalysis
from app.runs.models import SurveyRun
from app.templates.models import SurveyTemplate
from app.trace.enums import SpanKind
from app.trace.models import LLMRequest, LLMSpan


class InterpRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, span_id: UUID) -> InterpAnalysis | None:
        return await self.session.get(InterpAnalysis, span_id)

    async def store(self, row: InterpAnalysis) -> None:
        """Insert, leaving alone an analysis another request stored first.

        Two clicks on the same call can both run an analysis; the second result is the
        same reading of the same prompt, and the key would otherwise fail it.
        """
        values = {
            column.key: getattr(row, column.key) for column in InterpAnalysis.__table__.columns
        }
        stmt = (
            insert(InterpAnalysis).values(values).on_conflict_do_nothing(index_elements=["span_id"])
        )
        await self.session.execute(stmt)

    async def set_attribution(
        self,
        span_id: UUID,
        attribution: dict[str, Any],
        duration_ms: int,
        cost_usd: Decimal | None,
        attributed_at: datetime,
    ) -> None:
        await self.session.execute(
            update(InterpAnalysis)
            .where(InterpAnalysis.span_id == span_id)
            .values(
                attribution=attribution,
                attribution_ms=duration_ms,
                attribution_cost_usd=cost_usd,
                attributed_at=attributed_at,
            )
        )

    async def delete_for_run(self, run_id: UUID) -> None:
        """Explicit, because run_id is not a foreign key."""
        await self.session.execute(delete(InterpAnalysis).where(InterpAnalysis.run_id == run_id))

    async def attempt(self, span_id: UUID) -> LLMSpan | None:
        span = await self.session.get(LLMSpan, span_id)
        return span if span is not None and span.kind is SpanKind.attempt else None

    async def request(self, span_id: UUID) -> LLMRequest | None:
        return await self.session.get(LLMRequest, span_id)

    async def check_for(self, attempt: LLMSpan) -> LLMSpan | None:
        """The validation of the decision an attempt served: what the engine checked."""
        if attempt.parent_id is None:
            return None
        stmt = select(LLMSpan).where(
            LLMSpan.parent_id == attempt.parent_id, LLMSpan.kind == SpanKind.validation
        )
        return (await self.session.scalars(stmt)).first()

    async def captured(
        self, survey_id: UUID | None, run_id: UUID | None
    ) -> list[tuple[LLMRequest, LLMSpan, str, InterpAnalysis | None]]:
        """Every captured attempt in scope, oldest first, with its survey and any analysis."""
        stmt = (
            select(LLMRequest, LLMSpan, SurveyTemplate.title, InterpAnalysis)
            .join(LLMSpan, LLMSpan.id == LLMRequest.span_id)
            .join(SurveyRun, SurveyRun.id == LLMRequest.run_id)
            .join(SurveyTemplate, SurveyTemplate.id == SurveyRun.template_id)
            .outerjoin(InterpAnalysis, InterpAnalysis.span_id == LLMRequest.span_id)
            .order_by(LLMSpan.started_at)
        )
        if survey_id is not None:
            stmt = stmt.where(SurveyRun.template_id == survey_id)
        if run_id is not None:
            stmt = stmt.where(LLMRequest.run_id == run_id)
        # Plain tuples, because the outer join's analysis may be missing and the row type
        # the query builder infers says it never is.
        return [
            (request, span, title, analysis)
            for request, span, title, analysis in (await self.session.execute(stmt)).all()
        ]

    async def checks_for(self, parent_ids: list[UUID]) -> list[Row[Any]]:
        """The validation span under each of these decisions, in one query."""
        if not parent_ids:
            return []
        stmt = select(LLMSpan.parent_id, LLMSpan.attrs).where(
            LLMSpan.parent_id.in_(parent_ids), LLMSpan.kind == SpanKind.validation
        )
        return list((await self.session.execute(stmt)).all())
