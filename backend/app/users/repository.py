"""User queries."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.users.models import AccountChange, Function, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    def add(self, user: User) -> None:
        self.session.add(user)

    def add_change(self, change: AccountChange) -> None:
        """Append one audit row. There is no update or delete counterpart on purpose."""
        self.session.add(change)

    async def history_for(self, user_id: UUID) -> list[tuple[AccountChange, str | None]]:
        """This account's audit rows, newest first, each with its editor's name.

        The name is joined here rather than resolved per row by the caller, and it is a
        LEFT join: `changed_by` goes null when an administrator's account is deleted,
        and their edits must outlive them with "somebody" rather than vanish.

        Capped, because this backs a panel in a dialog rather than an export. The rows
        beyond the cap still exist; a screen that wants them can page when one exists.
        """
        editor = aliased(User)
        stmt = (
            select(AccountChange, editor.display_name)
            .outerjoin(editor, AccountChange.changed_by == editor.id)
            .where(AccountChange.user_id == user_id)
            .order_by(AccountChange.changed_at.desc(), AccountChange.id)
            .limit(50)
        )
        return [(change, name) for change, name in (await self.session.execute(stmt)).all()]

    async def all_changes(self, limit: int = 100) -> list[tuple[AccountChange, str | None]]:
        """Recent audit rows across every account, newest first.

        Capped because the screen is a witness, not an export.
        """
        editor = aliased(User)
        stmt = (
            select(AccountChange, editor.display_name)
            .outerjoin(editor, AccountChange.changed_by == editor.id)
            .order_by(AccountChange.changed_at.desc(), AccountChange.id)
            .limit(limit)
        )
        return [(change, name) for change, name in (await self.session.execute(stmt)).all()]

    async def get_by_email(self, email: str) -> User | None:
        """Exact match, because the service case-folds before it asks.

        Not `ilike`: folding on the way in is what makes one address one account, and a
        case-insensitive lookup here would paper over any row that got in before that.
        """
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_microsoft_id(self, microsoft_id: str) -> User | None:
        result = await self.session.execute(select(User).where(User.microsoft_id == microsoft_id))
        return result.scalars().first()

    async def list_all(self) -> list[User]:
        result = await self.session.execute(select(User).order_by(User.display_name))
        return list(result.scalars().all())

    async def functions_by_id(self) -> dict[UUID, Function | None]:
        """Every user's function, for deciding who is a colleague of whom.

        One query for the whole page rather than one per survey. The access rules are pure
        functions and so cannot fetch the author of the survey they are judging; the
        caller has to hand them that, and handing it over a row at a time is a query per
        row on a list page.

        Two columns for a plant's staff list, which is the same size argument
        `reach_by_audience` already makes about loading every user, and the same escape
        hatch applies when it stops being true.
        """
        result = await self.session.execute(select(User.id, User.function))
        return {user_id: function for user_id, function in result.all()}

    async def ids_in_function(self, function: Function | None) -> set[UUID]:
        """Who else shares this function, for the lists a colleague should see.

        An empty set for `None` rather than every user without a function: a person with
        no job has no colleagues, and the alternative would put every service account in
        one enormous shared team. Band is deliberately not filtered here: this feeds the
        query that *fetches* candidate surveys, and `may_list` holds the band rule, so
        narrowing here too would be a second copy of it.
        """
        if function is None:
            return set()
        result = await self.session.execute(select(User.id).where(User.function == function))
        return set(result.scalars().all())
