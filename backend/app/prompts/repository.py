"""Every query on prompt versions and activations, and on the spans that ran under them."""

from typing import Any

from sqlalchemy import Row, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.prompts.models import PromptActivation, PromptVersion
from app.trace.enums import SpanKind
from app.trace.models import LLMSpan
from app.users.models import User


class PromptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_version(self, version: PromptVersion) -> None:
        self.session.add(version)

    def add_activation(self, activation: PromptActivation) -> None:
        self.session.add(activation)

    async def active_name(self, family: str) -> str | None:
        """The most recently activated name, or None when nobody has switched it."""
        stmt = (
            select(PromptActivation.name)
            .where(PromptActivation.family == family)
            .order_by(PromptActivation.activated_at.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def version(self, name: str) -> PromptVersion | None:
        stmt = select(PromptVersion).where(PromptVersion.name == name)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def versions(self, family: str) -> list[tuple[PromptVersion, str | None]]:
        """Saved versions, oldest first, with their author's name.

        The name is outer-joined, and None when the author's account is gone: the version
        outlives them, as its foreign key's SET NULL says.
        """
        stmt = (
            select(PromptVersion, User.display_name)
            .outerjoin(User, User.id == PromptVersion.created_by)
            .where(PromptVersion.family == family)
            .order_by(PromptVersion.created_at)
        )
        return [(version, author) for version, author in (await self.session.execute(stmt)).all()]

    async def usage(self, family: str) -> tuple[dict[str, Row[Any]], dict[str, Any]]:
        """Per version name: turns and runs it served and their median wait, then its cost.

        Read from the trace, so a version that ran before spans existed shows no usage,
        which is unknown rather than unused.
        """
        turns = (
            select(
                LLMSpan.prompt_version,
                func.count().label("turns"),
                func.count(distinct(LLMSpan.run_id)).label("runs"),
                func.percentile_cont(0.5).within_group(LLMSpan.duration_ms).label("turn_ms_p50"),
            )
            .where(LLMSpan.kind == SpanKind.turn, LLMSpan.prompt_version.like(f"{family}_v%"))
            .group_by(LLMSpan.prompt_version)
        )
        costs = (
            select(LLMSpan.prompt_version, func.sum(LLMSpan.cost_usd).label("cost_usd"))
            .where(LLMSpan.kind == SpanKind.attempt, LLMSpan.prompt_version.like(f"{family}_v%"))
            .group_by(LLMSpan.prompt_version)
        )
        by_name = {row.prompt_version: row for row in (await self.session.execute(turns)).all()}
        cost = {
            row.prompt_version: row.cost_usd for row in (await self.session.execute(costs)).all()
        }
        return by_name, cost
