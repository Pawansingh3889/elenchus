"""Roles, the permissions they bundle, and who carries one.

Three tables, mirroring the shape `Hat`/`UserHat` already established for "a grant
beyond the job": a fixed, native-enum vocabulary (`Permission`), a set of them per row
(`RolePermission`, keyed the same way `UserHat` keys a hat to a person), and a join
table recording who carries which role (`UserRole`). A role definition is a live,
directly-editable fact like `User.band` rather than a versioned, append-only one like a
prompt: renaming what "Survey Auditor" means is an edit, not a new release, because
nothing durable (a ledger row, a trace span) is ever stamped with a role's name.
"""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Permission(str, enum.Enum):
    """The fixed vocabulary a role can bundle. One value per capability `app.access`
    actually gates, no more: a permission that maps to nothing a rule reads would be
    a grant of nothing, silently.

    Deliberately not a free-text action string ("survey:read") the way AWS IAM spells
    them: a typo in a string column would silently grant nothing rather than failing
    loudly, which is exactly the shrug CLAUDE.md's "fail loudly" rule exists to prevent.
    A native Postgres enum makes the vocabulary something the schema enforces, the way
    `Function`, `Band` and `Hat` already do.
    """

    # Site-wide authoring, the same reach as manager band and up: also feeds
    # `may_author`'s callers (colleague-hood, the `managers` audience), so granting it
    # makes a role-holder behave exactly as a manager-band person would for every rule
    # that already reads `may_author`.
    survey_author = "survey_author"
    # Edit (save, publish, close, summarise) any survey, not only one's own.
    survey_edit = "survey_edit"
    # See every survey in listings, not only what ownership/colleague-hood would show.
    survey_list = "survey_list"
    # Read individual runs and answers on any survey.
    results_read_rows = "results_read_rows"
    # Read counts and distributions on any survey, without the rows behind them.
    results_read_totals = "results_read_totals"
    # Full administrator access, the same reach as the IT function or the email
    # allowlist. Only an existing admin can create or assign a role carrying this
    # (enforced by `require_admin` gating every route in this domain), which is the
    # same cost `is_admin`'s function route already accepted: a grant of administration
    # that the database, not just a column, can now confer.
    admin_all = "admin_all"


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Who defined this role. SET NULL, like every audit-adjacent creator column here:
    # a role outlives the admin who made it.
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )

    permission_rows: Mapped[list["RolePermission"]] = relationship(
        back_populates="role", lazy="selectin", cascade="all, delete-orphan"
    )

    def __init__(self, **kw: object) -> None:
        """Start with an empty, *loaded* permission collection unless one was given.

        Same reason `User.__init__` seeds `hat_rows`: a `Role` built in Python and
        flushed without this has an unloaded collection, and the first read of
        `permissions` raises MissingGreenlet from inside a pure access rule.
        """
        kw.setdefault("permission_rows", [])
        super().__init__(**kw)

    @property
    def permissions(self) -> frozenset[Permission]:
        return frozenset(p.permission for p in self.permission_rows)


class RolePermission(Base):
    """One permission a role bundles. The pair is the primary key, exactly as
    `UserHat` keys one hat to one person: a permission cannot be listed twice on the
    same role, and no surrogate id has to be invented to say so."""

    __tablename__ = "role_permissions"

    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission: Mapped[Permission] = mapped_column(
        SAEnum(Permission, name="permission"), primary_key=True
    )

    role: Mapped[Role] = relationship(back_populates="permission_rows")


class UserRole(Base):
    """One person carrying one role. Owned by this domain rather than `app.users`,
    because a role is a full entity of its own here (created, renamed, deleted through
    this domain's own admin API) and not a small fixed vocabulary the way `Hat` is."""

    __tablename__ = "user_roles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # SET NULL, not CASCADE: a grant must outlive the admin who made it, the way an
    # AccountChange row does.
    granted_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )

    role: Mapped[Role] = relationship(lazy="selectin")
