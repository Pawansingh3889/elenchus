"""Role queries, and the grant rows that attach one to a person."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.roles.models import Role, UserRole


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, role: Role) -> None:
        self.session.add(role)

    async def get(self, role_id: UUID) -> Role | None:
        return await self.session.get(Role, role_id)

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(select(Role).where(Role.name == name))
        return result.scalars().first()

    async def list_all(self) -> list[Role]:
        return list((await self.session.execute(select(Role).order_by(Role.name))).scalars().all())

    async def delete(self, role: Role) -> None:
        await self.session.delete(role)

    async def grant_count(self, role_id: UUID) -> int:
        """How many accounts currently carry this role, for the delete guard."""
        result = await self.session.execute(
            select(UserRole).where(UserRole.role_id == role_id).limit(1)
        )
        return 1 if result.scalars().first() is not None else 0

    async def grant(self, user_id: UUID, role_id: UUID, granted_by: UUID) -> UserRole:
        """Attach a role to a person. Idempotent: attaching a role already held returns
        the existing grant rather than erroring, the way AWS's AttachRolePolicy does."""
        existing = await self.session.get(UserRole, (user_id, role_id))
        if existing is not None:
            return existing
        grant = UserRole(user_id=user_id, role_id=role_id, granted_by=granted_by)
        self.session.add(grant)
        return grant

    async def revoke(self, user_id: UUID, role_id: UUID) -> bool:
        """Detach a role from a person. Returns whether there was anything to detach."""
        existing = await self.session.get(UserRole, (user_id, role_id))
        if existing is None:
            return False
        await self.session.delete(existing)
        return True
