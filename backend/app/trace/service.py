"""What the lens pages read: traced runs, one run's spans, and totals across every run.

Admins only, asked here as well as at the route. Spans hold refusal reasons that can
quote a value a model proposed from a respondent's words, so the question is asked where
the data leaves the layer and not only at the door, which is also what
``check_access_consulted`` holds every service to.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.access import is_admin
from app.config import get_settings
from app.errors import ForbiddenError, NotFoundError
from app.trace.repository import SpanRepository
from app.trace.schemas import LensStrip, SpanRead, TierStrip, TracedRun
from app.users.models import User

ADMINS_ONLY = "The lens is for administrators: traces can quote what respondents said."


def _money(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


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
