"""Captured calls and their analyses: listed, read, and run on an administrator's request."""

import time
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import ValidationError as SchemaError
from sqlalchemy.ext.asyncio import AsyncSession

from app.access import is_admin
from app.config import get_settings
from app.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.interp.models import InterpAnalysis
from app.interp.repository import InterpRepository
from app.interp.schemas import (
    Analysis,
    AttributionResult,
    CapturedAsk,
    InterpStatus,
    StoredAnalysis,
    StoredAttribution,
)
from app.interp.transport import InterpTransport, InterpUnavailableError, get_transport
from app.llm import ledger
from app.trace.models import LLMRequest, LLMSpan
from app.users.models import User

ADMINS_ONLY = "The interpretability lens is for administrators: it reads what respondents typed."
# The tier number ledger rows carry for work outside the conduct chain.
OUTSIDE_THE_CHAIN = 0


def _tool_names(request: LLMRequest) -> list[str]:
    return [str(tool["function"]["name"]) for tool in request.tools]


def _money(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


class InterpService:
    def __init__(self, session: AsyncSession, transport: InterpTransport | None = None) -> None:
        self.session = session
        self.repo = InterpRepository(session)
        self._transport = transport

    @property
    def transport(self) -> InterpTransport:
        if self._transport is None:
            self._transport = get_transport()
        return self._transport

    def _require_admin(self, viewer: User) -> None:
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)

    async def status(self, viewer: User) -> InterpStatus:
        self._require_admin(viewer)
        if not get_settings().interp_enabled and self._transport is None:
            return InterpStatus(
                enabled=False,
                reachable=False,
                model=None,
                revision=None,
                device=None,
                detail="INTERP_ENABLED is off on this deployment.",
            )
        try:
            health = await self.transport.health()
        except InterpUnavailableError as exc:
            return InterpStatus(
                enabled=True,
                reachable=False,
                model=None,
                revision=None,
                device=None,
                detail=exc.message,
            )
        return InterpStatus(
            enabled=True,
            reachable=bool(health["ready"]),
            model=str(health["model"]),
            revision=str(health["revision"]),
            device=str(health["device"]),
            detail=None if health["ready"] else "The model is still loading.",
        )

    async def asks(
        self, viewer: User, survey_id: UUID | None, run_id: UUID | None
    ) -> list[CapturedAsk]:
        self._require_admin(viewer)
        rows = await self.repo.captured(survey_id, run_id)
        decisions = [
            attempt.parent_id for _, attempt, _, _ in rows if attempt.parent_id is not None
        ]
        checks = {parent: attrs for parent, attrs in await self.repo.checks_for(decisions)}
        asks = []
        for request, attempt, title, stored in rows:
            check = checks.get(attempt.parent_id) if attempt.error is None else None
            hosted_pick = None if check is None else check.get("tool")
            analysis = None if stored is None else Analysis.model_validate(stored.result)
            probability = None
            if analysis is not None and hosted_pick is not None:
                probability = next(
                    (t.probability for t in analysis.tools if t.name == hosted_pick), None
                )
            asks.append(
                CapturedAsk(
                    span_id=attempt.id,
                    run_id=request.run_id if request.run_id is not None else attempt.id,
                    survey_title=title,
                    started_at=attempt.started_at,
                    hosted_model=attempt.model,
                    tools_offered=_tool_names(request),
                    hosted_pick=hosted_pick,
                    outcome=None if check is None else check.get("outcome"),
                    hosted_ms=attempt.duration_ms,
                    hosted_prompt_tokens=attempt.prompt_tokens,
                    hosted_cost_usd=_money(attempt.cost_usd),
                    analysed=stored is not None,
                    attributed=stored is not None and stored.attribution is not None,
                    qwen_pick=None if analysis is None else analysis.pick,
                    qwen_probability_of_hosted_pick=probability,
                    agrees=(
                        None
                        if analysis is None or hosted_pick is None
                        else analysis.pick == hosted_pick
                    ),
                    analysis_ms=None if stored is None else stored.duration_ms,
                    analysis_cost_usd=None if stored is None else _money(stored.cost_usd),
                    attribution_ms=None if stored is None else stored.attribution_ms,
                    attribution_cost_usd=(
                        None if stored is None else _money(stored.attribution_cost_usd)
                    ),
                )
            )
        return asks

    async def analysis(self, viewer: User, span_id: UUID) -> StoredAnalysis:
        self._require_admin(viewer)
        stored = await self.repo.get(span_id)
        if stored is None:
            raise NotFoundError("That call has not been analysed yet.")
        return await self._read(stored)

    async def analyse(self, viewer: User, span_id: UUID) -> StoredAnalysis:
        """Read one captured call with the local model, once; later requests read the result."""
        self._require_admin(viewer)
        stored = await self.repo.get(span_id)
        if stored is not None:
            return await self._read(stored)
        attempt = await self.repo.attempt(span_id)
        if attempt is None:
            raise NotFoundError("No model call with that id.")
        request = await self.repo.request(span_id)
        if request is None:
            raise NotFoundError(
                "That call has no captured prompt: prompts are kept for calls made from "
                "13 Sep 2026 on."
            )
        check = None if attempt.error is not None else await self.repo.check_for(attempt)
        called = None if check is None else check.attrs.get("tool")
        # A call the engine refused because the tool was never offered has nothing to
        # explain among the offered tools, so it is read without attribution.
        target = called if called in _tool_names(request) else None

        started = time.monotonic()
        body = await self.transport.analyse({"messages": request.messages, "tools": request.tools})
        duration_ms = int((time.monotonic() - started) * 1000)
        try:
            analysis = Analysis.model_validate(body)
        except SchemaError as exc:
            raise InterpUnavailableError(
                "The interpretability service answered in a shape this backend does not "
                f"read: {exc}"
            ) from exc

        cost = self._book("interp", analysis.model, analysis.prompt_tokens, duration_ms)
        await self.repo.store(
            InterpAnalysis(
                span_id=span_id,
                run_id=request.run_id,
                model=analysis.model,
                revision=analysis.revision,
                device=analysis.device,
                target_tool=target,
                result=analysis.model_dump(mode="json"),
                duration_ms=duration_ms,
                cost_usd=None if cost is None else Decimal(str(cost)),
                created_at=datetime.now(UTC),
            )
        )
        await self.session.commit()
        stored = await self.repo.get(span_id)
        assert stored is not None, "an analysis just stored can be read back"
        return await self._read(stored)

    async def attribute(self, viewer: User, span_id: UUID) -> StoredAnalysis:
        """Attribute a read call's hosted pick to its prompt, once; later requests read it."""
        self._require_admin(viewer)
        stored = await self.repo.get(span_id)
        if stored is None:
            raise ConflictError(
                "Read this call before attributing it: the attribution is shown beside the "
                "reading it explains."
            )
        if stored.attribution is not None:
            return await self._read(stored)
        if stored.target_tool is None:
            raise ValidationError(
                "This call produced no offered tool the engine checked, so there is no choice "
                "to attribute."
            )
        request = await self.repo.request(span_id)
        if request is None:
            raise NotFoundError("That call's captured prompt is gone.")

        started = time.monotonic()
        body = await self.transport.attribute(
            {
                "messages": request.messages,
                "tools": request.tools,
                "target_tool": stored.target_tool,
            }
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        try:
            result = AttributionResult.model_validate(body)
        except SchemaError as exc:
            raise InterpUnavailableError(
                "The interpretability service answered in a shape this backend does not "
                f"read: {exc}"
            ) from exc
        cost = self._book("interp_attribution", result.model, result.prompt_tokens, duration_ms)
        await self.repo.set_attribution(
            span_id,
            result.model_dump(mode="json"),
            duration_ms,
            None if cost is None else Decimal(str(cost)),
            datetime.now(UTC),
        )
        await self.session.commit()
        await self.session.refresh(stored)
        return await self._read(stored)

    def _book(self, op: str, model: str, prompt_tokens: int, duration_ms: int) -> float | None:
        """A ledger row priced like any local tier, by wall clock against the machine's draw
        and tariff, so the spend file explains this work too. Returns the same cost."""
        economics = ledger.TierEconomics(
            params_b=get_settings().interp_params_b,
            local=True,
            price_in_per_mtok=None,
            price_out_per_mtok=None,
        )
        ledger.record(
            tier=OUTSIDE_THE_CHAIN,
            model=model,
            op=op,
            usage={"prompt_tokens": prompt_tokens, "completion_tokens": 0},
            latency_ms=duration_ms,
            status=200,
            priced_as=economics,
        )
        return ledger.cost_usd(economics, prompt_tokens, 0, duration_ms)

    async def _read(self, stored: InterpAnalysis) -> StoredAnalysis:
        attempt: LLMSpan | None = await self.repo.attempt(stored.span_id)
        return StoredAnalysis(
            span_id=stored.span_id,
            run_id=stored.run_id,
            target_tool=stored.target_tool,
            analysed_at=stored.created_at,
            duration_ms=stored.duration_ms,
            cost_usd=_money(stored.cost_usd),
            hosted_model=None if attempt is None else attempt.model,
            hosted_ms=0 if attempt is None else attempt.duration_ms,
            hosted_cost_usd=None if attempt is None else _money(attempt.cost_usd),
            analysis=Analysis.model_validate(stored.result),
            attribution=(
                None
                if stored.attribution is None
                or stored.attributed_at is None
                or stored.attribution_ms is None
                else StoredAttribution(
                    attributed_at=stored.attributed_at,
                    duration_ms=stored.attribution_ms,
                    cost_usd=_money(stored.attribution_cost_usd),
                    result=AttributionResult.model_validate(stored.attribution),
                )
            ),
        )
