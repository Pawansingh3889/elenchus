"""User model and the job vocabulary: one function, one band, any number of hats.

This replaced three older vocabularies at once (`UserRole`, `CreatorDepartment`,
`RespondentGroup`) and the free-form membership table that joined them. The old shape
let one person be recorded as a line leader and QA at the same time, which the plant's
own org chart says is not a thing: QA checks production's work, so QA independence is
structural, not a preference. The fix is the standard job-architecture one: every
person holds exactly one job, a (function, band) pair, and everything the app used to
store about them (role, department, groups) is derived from it. One job per person is
the schema-level version of an RBAC separation-of-duty constraint.
"""

import enum
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Function(str, enum.Enum):
    """Which ladder somebody is on: the departments of the plant, floor and office alike.

    One list rather than the old creator/respondent split, because the same question
    ("where does this person work") was being answered by two vocabularies that could
    disagree. The floor lives in `production`, `quality` and `health_safety`; the office
    is the rest. `it` stays because IT membership grants administration, a decision
    recorded on `is_admin`. `technical` is the spec-and-compliance office in the food
    industry's sense of the word, distinct from the QA ladder in `quality`.
    """

    production = "production"
    quality = "quality"
    health_safety = "health_safety"
    technical = "technical"
    planning = "planning"
    hr = "hr"
    finance = "finance"
    supply_chain = "supply_chain"
    it = "it"
    # Site leadership: the factory manager and the production director. A function of
    # its own rather than a band on `production`, because they stand over every ladder,
    # and the access rules give the band-qualified members of this one read access to
    # every survey.
    executive = "executive"


class Band(str, enum.Enum):
    """How high on the ladder. Ordered, and the order is load-bearing: authoring and
    the `managers` audience are both "manager band and up", read through BAND_RANK.

    The names are the floor's own words. `line_leader` means nothing outside
    production and simply goes unused elsewhere; inventing greyer words (associate,
    lead) so every function could use every band would trade the plant's vocabulary
    for an org chart nobody here works in. A QA technician on the floor is
    `quality`/`operative`, which is precisely the job title the industry uses.
    """

    operative = "operative"
    line_leader = "line_leader"
    supervisor = "supervisor"
    manager = "manager"
    head = "head"
    director = "director"


# The order, spelled out once. `list(Band)` would encode the same fact implicitly, but
# a reorder of the enum for readability would then silently change who may author.
BAND_RANK: dict[Band, int] = {
    Band.operative: 0,
    Band.line_leader: 1,
    Band.supervisor: 2,
    Band.manager: 3,
    Band.head: 4,
    Band.director: 5,
}


class Hat(str, enum.Enum):
    """A cross-cutting responsibility somebody carries on top of their job.

    The org chart's answer to "a supervisor with additional health and safety
    responsibility": the job stays production/supervisor, the H&S duty is a hat. A
    separate small vocabulary rather than a second job, because a hat grants being
    *asked* about the duty (the health_safety audience) and nothing else: no
    authoring, no colleague visibility, no band.
    """

    health_safety = "health_safety"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        # A job is a pair or nothing. Half a job (a function with no band, a band with
        # no function) is a row every rule would misread, so the schema refuses it.
        CheckConstraint(
            "(function IS NULL) = (band IS NULL)",
            name="ck_users_job_is_both_or_neither",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    # The Entra object id, for the people who sign in with Microsoft. Sign-in method
    # only: it decides nothing about what the account may do, which is `band`'s job.
    # The old intent for this column (its presence would decide who is a creator) died
    # with the role column: line leaders use the ERP and will hold logins without that
    # making them survey authors.
    #
    # Nullable because most of a plant signs in by link, and unique because two people
    # sharing one would be two people sharing an identity.
    microsoft_id: Mapped[str | None] = mapped_column(String(64), unique=True, default=None)
    # The job. Nullable as a pair (see the check constraint): a service or
    # administration account has no place on any ladder, is in no audience, and may
    # author nothing. Every real person has one.
    function: Mapped[Function | None] = mapped_column(
        SAEnum(Function, name="user_function"), default=None
    )
    band: Mapped[Band | None] = mapped_column(SAEnum(Band, name="user_band"), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # The administrator who made this account on the admin screen. Null for everyone the
    # screen did not create: the seeded accounts predate it, and the accounts a real Entra
    # sign-in will provision arrive from outside the app entirely. So this answers "who let
    # this person in", and a null is "nobody here did" rather than a missing value.
    #
    # Self-referential and deliberately not a relationship. Every reader wants a name to
    # print beside a row it already holds, and a relationship here would load a second User
    # per row down the same lazy path that raises MissingGreenlet inside the access rules,
    # which is the reason `hat_rows` below is `selectin`.
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )

    # `selectin` rather than lazy loading, and that is load-bearing rather than a tuning
    # choice. The access rules are pure functions of what they are handed, so the hats
    # have to be on the User by the time a rule reads them; a lazy relationship would
    # instead raise MissingGreenlet from inside a rule under async SQLAlchemy. One extra
    # query per load of users, and the one caller that loads every user is counting reach
    # over all of them anyway.
    hat_rows: Mapped[list["UserHat"]] = relationship(
        back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )

    def __init__(self, **kw: Any) -> None:
        """Start with an empty, *loaded* hats collection unless one was given.

        Without this, a `User` built in Python and flushed has an unloaded collection, and
        the first rule to read `hats` raises MissingGreenlet from inside a pure function
        under async SQLAlchemy. `lazy="selectin"` does not help there: it applies to
        objects a query loads, and this one was never queried for.

        SQLAlchemy does not call `__init__` when loading a row, so this cannot mask a real
        collection with an empty one.
        """
        kw.setdefault("hat_rows", [])
        super().__init__(**kw)

    @property
    def hats(self) -> frozenset[Hat]:
        """The hats this person carries, as a set, which is what every rule wants.

        A property over the rows rather than a second stored column: there is one source
        of truth and no way for the two to disagree.
        """
        return frozenset(h.hat for h in self.hat_rows)


class AccountChange(Base):
    """One admin edit to one account, written in the same transaction as the edit.

    Append-only, and the reason it exists is the live-reach decision: who a survey is for
    is whoever holds the job today, so denominators move when a job does, and this is the
    record that says who moved them. Deliberately no relationship back to User in
    either direction; the history is fetched by the one endpoint that wants it, not
    carried around on every person the directory loads.
    """

    __tablename__ = "account_changes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # SET NULL, both of them: an audit row that vanishes with its subject is not audit.
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    changed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # {kind: created|updated, before: {...}|null, after: {...}}. The snapshots hold the
    # fields an administrator controls, as the strings the enums store, so a row is
    # readable in psql without the application to decode it. Rows written before the job
    # model carry the old vocabulary (role, department, groups); they are history and are
    # served as written, never rewritten to today's shape.
    change: Mapped[dict[str, Any]] = mapped_column(JSONB)


class UserHat(Base):
    """One person carrying one cross-cutting responsibility.

    The pair is the primary key, so the same hat cannot be recorded twice and no
    surrogate id has to be invented to say so.
    """

    __tablename__ = "user_hats"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    hat: Mapped[Hat] = mapped_column(SAEnum(Hat, name="user_hat"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="hat_rows")
