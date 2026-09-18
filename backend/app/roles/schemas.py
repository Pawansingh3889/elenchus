"""Role admin API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.roles.models import Permission, Role


class RoleWrite(BaseModel):
    name: str = Field(max_length=200)
    permissions: list[Permission] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def _trim_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("permissions")
    @classmethod
    def _no_duplicates(cls, value: list[Permission]) -> list[Permission]:
        if len(set(value)) != len(value):
            # The role_permissions primary key is (role_id, permission), so a repeat is
            # otherwise an IntegrityError at flush, several layers too late to say which
            # field caused it.
            raise ValueError("The same permission is listed twice.")
        return value

    @model_validator(mode="after")
    def _check_the_name(self) -> "RoleWrite":
        if not self.name:
            raise ValueError("A role needs a name.")
        return self


class RoleRead(BaseModel):
    id: UUID
    name: str
    permissions: list[Permission]
    created_at: datetime
    created_by: UUID | None
    # Whether any account currently carries this role, so the admin API can explain a
    # refused delete without a second round trip.
    in_use: bool

    @classmethod
    def of(cls, role: Role, *, in_use: bool) -> "RoleRead":
        return cls(
            id=role.id,
            name=role.name,
            permissions=sorted(role.permissions, key=lambda p: p.value),
            created_at=role.created_at,
            created_by=role.created_by,
            in_use=in_use,
        )
