"""All queries for passes, durable allowances and the shared demo budget."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.demo.models import PLATFORM_WORKSPACE_ID, DemoAccess, DemoRegistry, DemoSpend, DemoUsage
from app.templates.models import SurveyTemplate
from app.workspaces.models import Workspace


class DemoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def access(self, *, lock: bool = False) -> DemoAccess | None:
        workspace = self.session.info.get("workspace_id")
        if workspace is None:
            return None
        stmt = select(DemoAccess).where(DemoAccess.workspace_id == workspace)
        if lock:
            stmt = stmt.with_for_update().execution_options(populate_existing=True)
        return (await self.session.scalars(stmt)).one_or_none()

    def add(self, row: DemoAccess | DemoRegistry | DemoUsage | DemoSpend | Workspace) -> None:
        self.session.add(row)

    async def usage(self, month: date) -> DemoUsage:
        stmt = select(DemoUsage).where(
            DemoUsage.workspace_id == self.session.info["workspace_id"],
            DemoUsage.month_start == month,
        )
        row = (await self.session.scalars(stmt)).one_or_none()
        if row is None:
            row = DemoUsage(month_start=month, sessions_started=0)
            self.session.add(row)
        return row

    async def usage_count(self, month: date) -> int:
        return (
            await self.session.scalar(
                select(DemoUsage.sessions_started).where(
                    DemoUsage.workspace_id == self.session.info["workspace_id"],
                    DemoUsage.month_start == month,
                )
            )
        ) or 0

    async def ensure_platform(self) -> None:
        await self.session.execute(
            insert(Workspace)
            .values(id=PLATFORM_WORKSPACE_ID, name="Elenchus demo operations")
            .on_conflict_do_nothing(index_elements=[Workspace.id])
        )

    async def lock_template(self, template_id: UUID) -> SurveyTemplate | None:
        stmt = select(SurveyTemplate).where(SurveyTemplate.id == template_id).with_for_update()
        return (
            await self.session.scalars(stmt.execution_options(populate_existing=True))
        ).one_or_none()

    async def registry(self) -> list[DemoRegistry]:
        return list(
            (
                await self.session.scalars(
                    select(DemoRegistry).order_by(DemoRegistry.issued_at.desc())
                )
            ).all()
        )

    async def registered(self, workspace_id: UUID) -> bool:
        return await self.session.get(DemoRegistry, workspace_id) is not None

    async def lock_budget(self) -> None:
        # ponytail: one short database lock for all demo reservations; shard after the pilot.
        await self.session.execute(text("SELECT pg_advisory_xact_lock(726092601)"))

    async def charged(self, month: date) -> Decimal:
        value = await self.session.scalar(
            select(
                func.coalesce(
                    func.sum(func.coalesce(DemoSpend.actual_usd, DemoSpend.reserved_usd)), 0
                )
            ).where(DemoSpend.month_start == month)
        )
        assert isinstance(value, Decimal)
        return value

    async def spend(self, spend_id: UUID) -> DemoSpend | None:
        return await self.session.get(DemoSpend, spend_id)

    async def spend_rows(self, month: date) -> list[DemoSpend]:
        return list(
            (
                await self.session.scalars(select(DemoSpend).where(DemoSpend.month_start == month))
            ).all()
        )
