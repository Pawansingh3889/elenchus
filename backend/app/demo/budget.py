"""Durable reservations at the transport boundary, including every retry and failover."""

import json
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import ROUND_CEILING, Decimal
from typing import Any

from app.config import get_settings
from app.db.session import SessionFactory
from app.demo.models import PLATFORM_WORKSPACE_ID, DemoSpend
from app.demo.policy import AllowanceError, active
from app.demo.repository import DemoRepository
from app.errors import ForbiddenError
from app.llm.ledger import TierEconomics
from app.workspaces.context import current_workspace

MILLION = Decimal(1000000)
PRECISION = Decimal("0.00000001")


@asynccontextmanager
async def reserve_attempt(
    payload: dict[str, Any], economics: TierEconomics | None
) -> AsyncIterator[dict[str, Any]]:
    result: dict[str, Any] = {}
    workspace_id = current_workspace.get()
    if workspace_id is None:
        yield result
        return
    async with SessionFactory(info={"workspace_id": workspace_id}) as tenant:
        access = await DemoRepository(tenant).access()
        if access is not None:
            active(access)
        demo = access is not None and access.customer_product is None
    if not demo:
        yield result
        return
    if not get_settings().demo_enabled:
        raise ForbiddenError("Paid demo work is not enabled on this deployment.")
    if (
        economics is None
        or economics.local
        or economics.price_in_per_mtok is None
        or economics.price_out_per_mtok is None
    ):
        raise ForbiddenError("This model has no bounded hosted price configured for demo use.")
    input_rate = Decimal(str(economics.price_in_per_mtok))
    output_rate = Decimal(str(economics.price_out_per_mtok))
    # UTF-8 byte length is a deliberately conservative bound, plus message framing.
    # Reserve uncached input even if the provider later discounts cached tokens.
    input_bound = len(json.dumps(payload, ensure_ascii=False).encode()) + 4096
    output_bound = payload.get("max_completion_tokens", 0)
    if not isinstance(output_bound, int) or output_bound < 0:
        raise ForbiddenError("The demo model request must have a bounded output length.")
    reserved = ((input_bound * input_rate + output_bound * output_rate) / MILLION).quantize(
        PRECISION, rounding=ROUND_CEILING
    )
    month = datetime.now(UTC).date().replace(day=1)
    async with SessionFactory(info={"workspace_id": PLATFORM_WORKSPACE_ID}) as platform:
        repo = DemoRepository(platform)
        await repo.lock_budget()
        if await repo.charged(month) + reserved > Decimal(
            str(get_settings().demo_monthly_budget_usd)
        ):
            raise AllowanceError(
                "The shared demo AI budget is used for this month. "
                "Your saved work remains available."
            )
        record = DemoSpend(
            demo_workspace_id=workspace_id,
            month_start=month,
            model=str(payload["model"]),
            reserved_usd=reserved,
        )
        repo.add(record)
        await platform.commit()
        reservation_id = record.id
    started = time.monotonic()
    failed = True
    try:
        yield result
        failed = False
    finally:
        actual: Decimal | None = None
        usage = result.get("usage")
        if isinstance(usage, dict):
            incoming, outgoing = usage.get("prompt_tokens"), usage.get("completion_tokens")
            if outgoing is None and "input" in payload:
                outgoing = 0
            if (
                isinstance(incoming, int)
                and isinstance(outgoing, int)
                and incoming >= 0
                and outgoing >= 0
            ):
                actual = ((incoming * input_rate + outgoing * output_rate) / MILLION).quantize(
                    PRECISION, rounding=ROUND_CEILING
                )
        async with SessionFactory(info={"workspace_id": PLATFORM_WORKSPACE_ID}) as platform:
            row = await DemoRepository(platform).spend(reservation_id)
            if row is None:
                raise RuntimeError("A committed demo reservation is missing.")
            row.actual_usd = actual
            row.failed = failed
            row.latency_ms = int((time.monotonic() - started) * 1000)
            await platform.commit()
