"""User model and role enum."""

import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(str, enum.Enum):
    author = "author"
    respondent = "respondent"


class CreatorDepartment(str, enum.Enum):
    """Which part of the business a creator belongs to, and the audience a survey can name.

    Grouping, not permission. What a user may *do* is still `role`, and admin rights come
    from the email allowlist in settings rather than from this field, so that an admin can
    also work in Finance and so that granting admin is never a database edit.

    `admin` is a member anyway, because the test and administration account has to belong
    somewhere and pretending it is in Operations would be a lie the dashboard repeats.
    """

    admin = "admin"
    hr = "hr"
    operations = "operations"
    finance = "finance"
    technical = "technical"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role"))
    # Nullable because a respondent has no department: they are one pool, and the site
    # attributes planned for them are a different mechanism. A *creator* without one is a
    # misconfiguration rather than a state, and access fails closed on it.
    department: Mapped[CreatorDepartment | None] = mapped_column(
        SAEnum(CreatorDepartment, name="creator_department"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
