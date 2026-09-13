"""Save a prompt as a new version, activate one, and resolve the live text for a turn.

Editable families are named, not inferred: conduct only, for now. The drafting, summary
and checker prompts stay files, versioned through pull requests.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.access import is_admin
from app.config import get_settings
from app.errors import ConflictError, ForbiddenError, NotFoundError
from app.llm.prompts import PROMPTS_DIR, PromptNotFoundError, load_prompt
from app.prompts.models import PromptActivation, PromptVersion
from app.prompts.repository import PromptRepository
from app.prompts.schemas import PromptBodyRead, PromptFamilyRead, PromptVersionRead
from app.users.models import User

# Each editable family and the version the code names for it.
EDITABLE = {"conduct": "conduct_v8"}
ADMINS_ONLY = (
    "Prompts are changed by administrators: a prompt decides what every respondent is asked."
)


@dataclass(frozen=True)
class ResolvedPrompt:
    name: str
    text: str


def _number(name: str) -> int:
    match = re.search(r"_v(\d+)$", name)
    if match is None:
        raise ValueError(f"not a versioned prompt name: {name!r}")
    return int(match.group(1))


def _file_versions(family: str, directory: Path = PROMPTS_DIR) -> list[str]:
    return sorted(
        (
            p.stem
            for p in directory.glob(f"{family}_v*.md")
            if re.fullmatch(rf"{family}_v\d+", p.stem)
        ),
        key=_number,
    )


class PromptResolver:
    """The live prompt for a family, for the engine. No viewer: this is not a read by a person."""

    def __init__(self, session: AsyncSession) -> None:
        self.repo = PromptRepository(session)

    async def active(self, family: str, default: str) -> ResolvedPrompt:
        name = await self.repo.active_name(family) or default
        return ResolvedPrompt(name, await self.text(name))

    async def text(self, name: str) -> str:
        """A file version first, then a saved one. Missing from both fails loudly."""
        try:
            return load_prompt(name)
        except PromptNotFoundError:
            saved = await self.repo.version(name)
            if saved is None:
                raise
            return saved.body


class PromptAdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PromptRepository(session)
        self.resolver = PromptResolver(session)

    def _family(self, family: str) -> str:
        if family not in EDITABLE:
            raise NotFoundError(f"The {family!r} prompt is not editable here; only conduct is.")
        return EDITABLE[family]

    async def family(self, viewer: User, family: str) -> PromptFamilyRead:
        """Every version of a family, file and saved, oldest first, with what each cost."""
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)
        default = self._family(family)
        active = await self.repo.active_name(family) or default
        usage, cost = await self.repo.usage(family)

        def read(
            name: str,
            source: Literal["file", "database"],
            created_at: datetime | None,
            author: str | None,
            note: str | None,
        ) -> PromptVersionRead:
            row = usage.get(name)
            spent = cost.get(name)
            return PromptVersionRead(
                name=name,
                source=source,
                active=name == active,
                created_at=created_at,
                created_by_name=author,
                note=note,
                turns=row.turns if row is not None else None,
                runs=row.runs if row is not None else None,
                turn_ms_p50=row.turn_ms_p50 if row is not None else None,
                cost_usd=float(spent) if isinstance(spent, Decimal) else None,
            )

        versions = [read(name, "file", None, None, None) for name in _file_versions(family)]
        for saved, author in await self.repo.versions(family):
            versions.append(read(saved.name, "database", saved.created_at, author, saved.note))
        return PromptFamilyRead(family=family, active=active, default=default, versions=versions)

    async def body(self, viewer: User, family: str, name: str) -> PromptBodyRead:
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)
        self._family(family)
        if not name.startswith(f"{family}_v"):
            raise NotFoundError(f"{name!r} is not a {family} prompt.")
        source = "file" if name in _file_versions(family) else "database"
        try:
            text = await self.resolver.text(name)
        except PromptNotFoundError as exc:
            raise NotFoundError(f"No {family} prompt is named {name!r}.") from exc
        return PromptBodyRead(name=name, source=source, body=text)

    async def save(
        self, viewer: User, family: str, body: str, note: str | None
    ) -> PromptFamilyRead:
        """Save the text as the next version. Saving does not activate it."""
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)
        self._family(family)
        text = body.strip()
        saved = [v for v, _ in await self.repo.versions(family)]
        names = _file_versions(family) + [v.name for v in saved]
        latest = max(names, key=_number)
        if text == (await self.resolver.text(latest)).strip():
            raise ConflictError(f"This text is identical to {latest}; nothing to save.")
        self.repo.add_version(
            PromptVersion(
                family=family,
                name=f"{family}_v{_number(latest) + 1}",
                body=text,
                note=(note or "").strip() or None,
                created_by=viewer.id,
            )
        )
        await self.session.commit()
        return await self.family(viewer, family)

    async def activate(self, viewer: User, family: str, name: str) -> PromptFamilyRead:
        """Make a version live from the next turn. Rolling back is activating an older one."""
        if not is_admin(viewer, get_settings().admin_email_set):
            raise ForbiddenError(ADMINS_ONLY)
        self._family(family)
        known = _file_versions(family) + [v.name for v, _ in await self.repo.versions(family)]
        if name not in known:
            raise NotFoundError(f"No {family} prompt is named {name!r}.")
        self.repo.add_activation(PromptActivation(family=family, name=name, activated_by=viewer.id))
        await self.session.commit()
        return await self.family(viewer, family)
