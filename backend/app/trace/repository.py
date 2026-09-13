"""Span writes and reads. The only module that queries llm_spans."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.trace.models import LLMSpan


class SpanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_all(self, spans: list[LLMSpan]) -> None:
        self.session.add_all(spans)

    async def for_run(self, run_id: UUID) -> list[LLMSpan]:
        stmt = select(LLMSpan).where(LLMSpan.run_id == run_id).order_by(LLMSpan.started_at)
        return list((await self.session.scalars(stmt)).all())

    async def delete_for_run(self, run_id: UUID) -> None:
        """Explicit, because run_id is not a foreign key (see the models docstring)."""
        await self.session.execute(delete(LLMSpan).where(LLMSpan.run_id == run_id))
