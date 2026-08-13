"""User request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.templates.enums import SurveyAudience
from app.users.models import CreatorDepartment, RespondentGroup, User, UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str
    role: UserRole


class PersonRead(BaseModel):
    """One person as the directory shows them: who they are, and where they sit.

    Deliberately not `UserRead` with fields bolted on. That one backs the development
    auth picker, where a user's id is their credential and the router is not mounted in
    production at all; this one is a product feature that has to exist in a deployment.
    Two schemas because they answer to two different lifetimes.

    No email. The question this page exists to answer is "who are the two people that
    survey reached", and a name, a department and a set of groups answer it. An address
    is contactable personal data that nothing on the page needs.
    """

    id: UUID
    display_name: str
    role: UserRole
    department: CreatorDepartment | None
    groups: list[RespondentGroup]
    # Whether this account carries an Entra object id, not the id itself. The screen uses
    # it to mark an author who has none, because such an account can build surveys today
    # and cannot sign in the day `role` is derived from that id instead of stored. A
    # boolean rather than the value because the page only ever asks "is one set".
    has_microsoft_id: bool

    @classmethod
    def of(cls, user: User) -> "PersonRead":
        return cls(
            id=user.id,
            display_name=user.display_name,
            role=user.role,
            department=user.department,
            has_microsoft_id=user.microsoft_id is not None,
            # Sorted, because `User.groups` is a set and sets have no order. Without this
            # a person's badges could shuffle between refreshes for no reason a reader
            # could see, which reads as the data changing when nothing has.
            groups=sorted(user.groups, key=lambda g: g.value),
        )


class IdentifyRequest(BaseModel):
    """An address, to trade for the id that stands in for a session.

    Scaffolding for the development shim and should not outlive it, like the user list
    it exists beside.
    """

    email: str = Field(max_length=320)


class MeRead(BaseModel):
    """The caller, as the caller. Chiefly: may they administer anything.

    A separate endpoint rather than a field on the user list, because the frontend
    currently works out who it is by scanning `/api/v1/users`, and that router is not
    mounted outside development at all. Admin cannot be derived client-side either: half
    of `is_admin` is an email allowlist that lives in server settings and is deliberately
    not shipped to a browser.
    """

    id: UUID
    display_name: str
    role: UserRole
    department: CreatorDepartment | None
    is_admin: bool


class AccountWrite(BaseModel):
    """What an administrator sets on an account, and the states that are refused.

    Every rule below is a 422 rather than a quiet correction. Each one describes a row
    that the access rules would go on to read as something nobody intended, and the point
    of refusing at this boundary is that the mistake is visible while somebody is still
    looking at the form that made it.

    `role` is taken from the request and stored as sent. That was chosen knowingly and it
    is worth naming the cost, because `app/users/models.py` records the opposite intent:
    an Entra object id is meant to *decide* `role` once real sign-in exists. So an author
    created here with no `microsoft_id` is somebody who may build surveys today and will
    silently stop being able to the day that derivation is switched on. The field is
    settable here so the two can be kept in step by whoever is filling the form, and the
    people directory marks the accounts where they are not.
    """

    # No `min_length` on the name, and none on the email in `AccountCreate` either. The
    # constraint would fire before the validators below and answer in Pydantic's own
    # voice: somebody who clicks Save on an empty form reads "display_name: String should
    # have at least 1 character", which names a field they never saw and describes a
    # string rather than a person. The checks live in the model validator instead, where
    # the sentence stands on its own and the client renders it unprefixed.
    display_name: str = Field(max_length=200)
    role: UserRole
    microsoft_id: str | None = Field(default=None, max_length=64)
    department: CreatorDepartment | None = None
    groups: list[RespondentGroup] = Field(default_factory=list)

    @field_validator("display_name")
    @classmethod
    def _trim_name(cls, value: str) -> str:
        """Trim only. Whether what is left is a name is the model validator's question."""
        return value.strip()

    @field_validator("microsoft_id")
    @classmethod
    def _blank_entra_id_means_none(cls, value: str | None) -> str | None:
        """An empty Entra id is absent, not empty.

        A form posts "" for a field somebody tabbed through, and "" is not a Microsoft
        account. Stored as written it would occupy the unique index, and the *second*
        account created without one would come back as a 409 naming a field nobody filled.
        """
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def _check_the_shape_of_this_person(self) -> "AccountWrite":
        if not self.display_name:
            # Reached by an empty box and by one holding only spaces. Both render as an
            # empty cell in every list the person appears in.
            raise ValueError("A name is required.")

        if len(set(self.groups)) != len(self.groups):
            # The membership primary key is (user_id, group), so a repeat is otherwise an
            # IntegrityError at flush: the same refusal, several layers too late to say
            # which field caused it.
            raise ValueError("The same group is listed twice.")

        if self.role is UserRole.author:
            if self.department is None:
                # CLAUDE.md: a creator without a department is a misconfiguration rather
                # than a state. It decides who their colleagues are and, for `it`, whether
                # they administer the system.
                raise ValueError(
                    "An author needs a department: it decides who their colleagues are."
                )
        else:
            if self.department is not None:
                # The load-bearing one. `_colleague` in app/access/rules.py makes anyone
                # sharing a department a colleague, and `may_read_rows` hands a colleague
                # every individual answer. A respondent given a department would quietly
                # gain the raw answers to every survey that department wrote, which is the
                # exact opposite of what the pseudonymity elsewhere promises them.
                raise ValueError(
                    "Only an author has a department. Giving one to somebody who answers "
                    "surveys would let them read their department's answers."
                )
            if not self.groups:
                # Somebody in no group can be asked nothing at all, not even a survey
                # aimed at everyone: `may_answer` refuses an empty `user.groups` on the
                # everyone branch. An account like that is a person nobody can survey.
                raise ValueError(
                    "Somebody who answers surveys needs at least one group, or no survey "
                    "can reach them."
                )
        return self


class AccountCreate(AccountWrite):
    """A new account. Email only appears here, and never on the update: see AccountUpdate."""

    email: str = Field(max_length=320)

    @field_validator("email")
    @classmethod
    def _fold(cls, value: str) -> str:
        """Case-fold, so one address is one account.

        `is_admin` folds both sides when it matches the allowlist; the unique index does
        not. Without this, `Ava@x.dev` and `ava@x.dev` are two rows, two identities, and
        one allowlist entry letting both administer.
        """
        return value.strip().casefold()

    @model_validator(mode="after")
    def _check_the_address(self) -> "AccountCreate":
        """Enough of a shape check to catch a typed mistake, and no more.

        Deliberately not RFC 5322: a full grammar would be a dependency and a false sense
        of precision. What this catches is the empty box and the address with no `@`,
        which are the mistakes a person actually makes while typing into a form.

        On the model rather than the field so the sentence reaches the reader whole. A
        field validator's complaint arrives labelled with the attribute name, and "email:
        That does not look like an email address" is the same sentence wearing jargon.
        """
        local, sep, domain = self.email.partition("@")
        if not sep or not local or "." not in domain:
            raise ValueError("That does not look like an email address.")
        return self


class AccountUpdate(AccountWrite):
    """A full replacement of the account, and deliberately without the email.

    Full replacement follows `TemplateUpdate`, and for the reason recorded there: a body
    that may omit a field is how a client that forgot one silently changes it. Sending
    every field each time turns that into a 422 somebody can see.

    Email is absent because `is_admin` matches the allowlist on it. Editing an address
    would be a way to hand somebody administration, or take it away, through a field that
    looks like a typo correction. Changing an address is a thing to build on purpose,
    with its own confirmation, rather than something that falls out of this form.
    """


class AccountSnapshot(BaseModel):
    """The fields an administrator controls, as one audit row records them.

    Email is absent because it cannot be edited, so it never differs between before and
    after; the row's `user_id` is the durable link to the account it describes.
    """

    display_name: str
    role: UserRole
    department: CreatorDepartment | None
    microsoft_id: str | None
    groups: list[RespondentGroup]

    @classmethod
    def of(cls, user: User) -> "AccountSnapshot":
        return cls(
            display_name=user.display_name,
            role=user.role,
            department=user.department,
            microsoft_id=user.microsoft_id,
            groups=sorted(user.groups, key=lambda g: g.value),
        )


class AccountChangeRead(BaseModel):
    """One audit row as the admin screen shows it.

    `changed_by_name` rather than an id the client would have to resolve, and nullable
    because edits must outlive their editor: a null renders as "an administrator", which
    is true, rather than the row disappearing, which would be an audit trail with holes.
    """

    id: UUID
    changed_at: datetime
    changed_by: UUID | None
    changed_by_name: str | None
    kind: str
    before: AccountSnapshot | None
    after: AccountSnapshot


class SurveyImpact(BaseModel):
    """One open survey whose audience this edit changes, and by how much.

    `reach_before`/`reach_after` differ by exactly one, because a preview considers one
    person's change. Sent as two numbers rather than a delta so the screen can print the
    honest pair ("3 -> 2") without arithmetic of its own.
    """

    template_id: UUID
    title: str
    audience: SurveyAudience
    # Whether this person is in the survey's audience after the edit. False reads as
    # "they can no longer answer it", true as "they can now answer it".
    now_in: bool
    reach_before: int
    reach_after: int


class AccountImpact(BaseModel):
    """What saving this edit would change, computed before anything is saved.

    The guardrail for live reach: membership edits move every open survey's denominator
    the moment they land, so the moment before is when the mover should see it. Warn and
    proceed rather than block, by decision: people genuinely leave teams, and a survey's
    reach dropping is then the truth, not a mistake to prevent.
    """

    groups_added: list[RespondentGroup]
    groups_removed: list[RespondentGroup]
    role_before: UserRole
    role_after: UserRole
    department_before: CreatorDepartment | None
    department_after: CreatorDepartment | None
    surveys: list[SurveyImpact]


class AccountRead(BaseModel):
    """An account as the administrator who just wrote it sees it.

    Carries the email, unlike `PersonRead`, which withholds it on the grounds that the
    directory does not need contactable personal data to answer "who is in this audience".
    This is the reply to a write by the person who typed that address, and showing back
    what was stored, folded case and all, is how they see it landed as intended.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str
    role: UserRole
    department: CreatorDepartment | None
    microsoft_id: str | None
    created_by: UUID | None
    groups: list[RespondentGroup]

    @classmethod
    def of(cls, user: User) -> "AccountRead":
        return cls(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            department=user.department,
            microsoft_id=user.microsoft_id,
            created_by=user.created_by,
            groups=sorted(user.groups, key=lambda g: g.value),
        )
