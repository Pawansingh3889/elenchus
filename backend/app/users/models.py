"""User model, role enum, department enum, and plant-floor group membership."""

import enum
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, enum.Enum):
    author = "author"
    respondent = "respondent"


class CreatorDepartment(str, enum.Enum):
    """Which part of the business a creator belongs to, and who else sees their surveys.

    Two jobs. It groups authors so that colleagues in one department can pick up each
    other's surveys and read what came back, and for `it` it grants administration.

    That second job reverses an earlier decision, recorded here rather than lost: admin
    used to come only from the email allowlist in settings, so that granting it was never
    a database edit. It is now also every member of `it`, which was asked for directly.
    The allowlist still works, so an admin who does not work in IT is still possible.
    """

    hr = "hr"
    finance = "finance"
    technical = "technical"
    management = "management"
    it = "it"


class RespondentGroup(str, enum.Enum):
    """What someone does on the plant floor, and the audience a survey can name.

    Membership in a table rather than a column, because these overlap in real life: a line
    leader who also covers QA is in both, and one column would force a choice that is not
    true. See `UserGroupMembership`.

    Separate from `CreatorDepartment` for the same reason that enum stays separate from
    `SurveyAudience`: "which office team is this person in" and "what do they do on the
    line" are different questions. A manager has a Teams login and so an author account,
    and still answers surveys aimed at managers, which is exactly why answering is decided
    by membership here and not by `role`.
    """

    operatives = "operatives"
    line_leaders = "line_leaders"
    supervisors = "supervisors"
    managers = "managers"
    qa = "qa"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role"))
    # Nullable because someone who only answers surveys has no office department: what
    # they do on the line is `memberships` instead. A *creator* without one is a
    # misconfiguration rather than a state, and access fails closed on it.
    department: Mapped[CreatorDepartment | None] = mapped_column(
        SAEnum(CreatorDepartment, name="creator_department"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # `selectin` rather than lazy loading, and that is load-bearing rather than a tuning
    # choice. The access rules are pure functions of what they are handed, so the groups
    # have to be on the User by the time a rule reads them; a lazy relationship would
    # instead raise MissingGreenlet from inside a rule under async SQLAlchemy. One extra
    # query per load of users, and the one caller that loads every user is counting reach
    # over all of them anyway.
    memberships: Mapped[list["UserGroupMembership"]] = relationship(
        back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )

    def __init__(self, **kw: Any) -> None:
        """Start with an empty, *loaded* membership collection unless one was given.

        Without this, a `User` built in Python and flushed has an unloaded collection, and
        the first rule to read `groups` raises MissingGreenlet from inside a pure function
        under async SQLAlchemy. `lazy="selectin"` does not help there: it applies to
        objects a query loads, and this one was never queried for.

        SQLAlchemy does not call `__init__` when loading a row, so this cannot mask a real
        collection with an empty one.
        """
        kw.setdefault("memberships", [])
        super().__init__(**kw)

    @property
    def groups(self) -> frozenset[RespondentGroup]:
        """The groups this person is in, as a set, which is what every rule wants.

        A property over the rows rather than a second stored column: there is one source
        of truth and no way for the two to disagree.
        """
        return frozenset(m.group for m in self.memberships)


class UserGroupMembership(Base):
    """One person's membership of one plant-floor group.

    The pair is the primary key, so the same person cannot be recorded in `operatives`
    twice and no surrogate id has to be invented to say so.
    """

    __tablename__ = "user_group_memberships"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    group: Mapped[RespondentGroup] = mapped_column(
        SAEnum(RespondentGroup, name="respondent_group"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="memberships")
