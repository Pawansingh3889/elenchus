"""User queries."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import CreatorDepartment, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def list_all(self) -> list[User]:
        result = await self.session.execute(select(User).order_by(User.display_name))
        return list(result.scalars().all())

    async def departments_by_id(self) -> dict[UUID, CreatorDepartment | None]:
        """Every user's department, for deciding who is a colleague of whom.

        One query for the whole page rather than one per survey. The access rules are pure
        functions and so cannot fetch the author of the survey they are judging; the
        caller has to hand them that, and handing it over a row at a time is a query per
        row on a list page.

        Two columns for a plant's staff list, which is the same size argument
        `_reach_by_audience` already makes about loading every user, and the same escape
        hatch applies when it stops being true.
        """
        result = await self.session.execute(select(User.id, User.department))
        return {user_id: department for user_id, department in result.all()}

    async def ids_in_department(self, department: CreatorDepartment | None) -> set[UUID]:
        """Who else is in this department, for the lists a colleague should see.

        An empty set for `None` rather than every user without a department: a person with
        no department has no colleagues, and the alternative would put every respondent in
        one enormous shared team.
        """
        if department is None:
            return set()
        result = await self.session.execute(select(User.id).where(User.department == department))
        return set(result.scalars().all())
