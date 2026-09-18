"""Role business logic: defining a bundle of permissions, and attaching it to a person.

Two different things live here, and the split matters. Defining what a role *means*
(its name, its permission set) is this domain's own concern. Attaching one to an
account is also handled here rather than folded into `UserService.replace_account`,
deliberately: `AccountUpdate` is a careful full-replacement of everything an
administrator controls about a *job*, with its own self-lockout and live-reach-preview
machinery, and a role grant is not a property of the job at all. Attach/detach is its
own pair of actions, the way AWS's AttachRolePolicy/DetachRolePolicy are their own
actions rather than a field on UpdateUser.
"""

import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ConflictError, NotFoundError
from app.roles.models import Role, RolePermission
from app.roles.repository import RoleRepository
from app.roles.schemas import RoleRead, RoleWrite
from app.users.models import AccountChange, User
from app.users.repository import UserRepository

logger = logging.getLogger("app.roles")


class RoleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = RoleRepository(session)
        self.users = UserRepository(session)

    async def list_roles(self) -> list[RoleRead]:
        roles = await self.repo.list_all()
        return [
            RoleRead.of(role, in_use=bool(await self.repo.grant_count(role.id))) for role in roles
        ]

    async def get_role(self, role_id: UUID) -> RoleRead:
        role = await self._require(role_id)
        return RoleRead.of(role, in_use=bool(await self.repo.grant_count(role.id)))

    async def create_role(self, data: RoleWrite, admin: User) -> RoleRead:
        role = Role(
            name=data.name,
            created_by=admin.id,
            permission_rows=[RolePermission(permission=p) for p in data.permissions],
        )
        self.repo.add(role)
        await self._commit_or_conflict(data.name)
        logger.info("role created: role=%s name=%s by=%s", role.id, role.name, admin.id)
        return RoleRead.of(role, in_use=False)

    async def replace_role(self, role_id: UUID, data: RoleWrite, admin: User) -> RoleRead:
        """Full replacement, matching `RoleWrite`. Reassigning `permission_rows` is what
        *removes* the permissions no longer listed, the same trade `AccountUpdate`
        makes for hats: a patch that only ever added would make narrowing a role's
        reach through this screen impossible."""
        role = await self._require(role_id)
        role.name = data.name
        role.permission_rows = [RolePermission(permission=p) for p in data.permissions]
        await self._commit_or_conflict(data.name)
        logger.info("role changed: role=%s name=%s by=%s", role.id, role.name, admin.id)
        return RoleRead.of(role, in_use=bool(await self.repo.grant_count(role.id)))

    async def delete_role(self, role_id: UUID) -> None:
        """Refuses while any account carries the role, for the same reason a survey
        with any run refuses deletion: a grant somebody is relying on is not a row to
        make vanish out from under them."""
        role = await self._require(role_id)
        if await self.repo.grant_count(role.id):
            raise ConflictError(
                f"{role.name!r} is granted to at least one account; revoke it from "
                "everyone who carries it before deleting the role."
            )
        await self.repo.delete(role)
        await self.session.commit()

    async def grant(self, user_id: UUID, role_id: UUID, admin: User) -> RoleRead:
        user = await self.users.get(user_id)
        if user is None:
            raise NotFoundError("No such account.")
        role = await self._require(role_id)
        await self.repo.grant(user_id, role_id, admin.id)
        self.users.add_change(
            AccountChange(
                user_id=user_id,
                changed_by=admin.id,
                change={"kind": "role_granted", "role": role.name},
            )
        )
        await self.session.commit()
        logger.info("role granted: user=%s role=%s by=%s", user_id, role_id, admin.id)
        return RoleRead.of(role, in_use=True)

    async def revoke(self, user_id: UUID, role_id: UUID, admin: User) -> None:
        user = await self.users.get(user_id)
        if user is None:
            raise NotFoundError("No such account.")
        role = await self._require(role_id)
        changed = await self.repo.revoke(user_id, role_id)
        if changed:
            self.users.add_change(
                AccountChange(
                    user_id=user_id,
                    changed_by=admin.id,
                    change={"kind": "role_revoked", "role": role.name},
                )
            )
        await self.session.commit()
        logger.info("role revoked: user=%s role=%s by=%s", user_id, role_id, admin.id)

    async def _require(self, role_id: UUID) -> Role:
        role = await self.repo.get(role_id)
        if role is None:
            raise NotFoundError("No such role.")
        return role

    async def _commit_or_conflict(self, name: str) -> None:
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            logger.info("role write lost a race, or the name is taken: %s", exc)
            raise ConflictError(f"A role named {name!r} already exists.") from exc
