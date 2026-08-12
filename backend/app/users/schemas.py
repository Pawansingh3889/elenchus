"""User response schemas."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

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

    @classmethod
    def of(cls, user: User) -> "PersonRead":
        return cls(
            id=user.id,
            display_name=user.display_name,
            role=user.role,
            department=user.department,
            # Sorted, because `User.groups` is a set and sets have no order. Without this
            # a person's badges could shuffle between refreshes for no reason a reader
            # could see, which reads as the data changing when nothing has.
            groups=sorted(user.groups, key=lambda g: g.value),
        )
