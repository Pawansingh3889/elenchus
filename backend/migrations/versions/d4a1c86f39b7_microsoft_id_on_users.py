"""microsoft id on users

Revision ID: d4a1c86f39b7
Revises: c7f2a91d84be
Create Date: 2026-08-12 23:05:00.000000

The identity half of the rollout, ahead of the sign-in that will use it. Creators hold
Microsoft accounts and the floor does not, so the presence of an Entra object id is what
will decide whether somebody may build surveys.

Nothing reads it yet. `users.role` is still the column the app asks, because the
development header shim stands in for a login; this is the field that replaces it, added
now so the accounts can carry the right data before the mechanism arrives.

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4a1c86f39b7"
down_revision: str | None = "c7f2a91d84be"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("microsoft_id", sa.String(length=64), nullable=True))
    # Unique, and nullable alongside it: Postgres allows any number of NULLs in a unique
    # index, which is exactly right here. Most of a plant has no Microsoft account, and
    # two people sharing one object id would be two people sharing an identity.
    op.create_unique_constraint("uq_users_microsoft_id", "users", ["microsoft_id"])


def downgrade() -> None:
    op.drop_constraint("uq_users_microsoft_id", "users", type_="unique")
    op.drop_column("users", "microsoft_id")
