"""created by on users

Revision ID: e8b3f60c9d47
Revises: d4a1c86f39b7
Create Date: 2026-08-13 10:40:00.000000

Who let this person in. Accounts were only ever made by the seed script or by hand
against the database, so the question had one answer and nowhere to record it; the admin
screen this ships alongside makes it a real question with more than one.

Nullable, and it will stay mostly null for a while. Every account that exists today was
created before the screen, and the accounts a real Microsoft sign-in will provision come
from outside the app, so a null here means "nobody in this app created this" rather than
a value somebody forgot to fill in.

SET NULL rather than CASCADE on delete: an administrator leaving must not take the floor
accounts they created with them.

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e8b3f60c9d47"
down_revision: str | None = "d4a1c86f39b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("created_by", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_users_created_by_users",
        "users",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_created_by_users", "users", type_="foreignkey")
    op.drop_column("users", "created_by")
