"""roles and permissions

Revision ID: a60cc4dbc330
Revises: 9b3e1d7a5c20
Create Date: 2026-09-18 00:00:00.000000

IAM-shaped, additive-only grants that sit beside the job (function/band/hats): a role
is a named, admin-defined bundle of `Permission`s, attached to any account regardless
of its job. See app/roles/models.py and app/access/__init__.py.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a60cc4dbc330"
down_revision: str | None = "9b3e1d7a5c20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERMISSION = sa.Enum(
    "survey_author",
    "survey_edit",
    "survey_list",
    "results_read_rows",
    "results_read_totals",
    "admin_all",
    name="permission",
)


def upgrade() -> None:
    # No explicit `PERMISSION.create()` here: unlike `follow_up_policy` (added via
    # `op.add_column` on an existing table, which does not fire the enum's own
    # "on table create" DDL event), this type is first used inside `op.create_table`
    # below, which creates it itself. Calling `.create()` first and then embedding the
    # same `PERMISSION` object in the column both attempt the CREATE TYPE, and the
    # second one is not checked first: it fails with a duplicate-type error rather
    # than being skipped.
    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_roles_created_by_users"), ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("permission", PERMISSION, nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name=op.f("fk_role_permissions_role_id_roles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("role_id", "permission", name=op.f("pk_role_permissions")),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column(
            "granted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("granted_by", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_user_roles_user_id_users"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.id"], name=op.f("fk_user_roles_role_id_roles"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["granted_by"],
            ["users.id"],
            name=op.f("fk_user_roles_granted_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("user_id", "role_id", name=op.f("pk_user_roles")),
    )


def downgrade() -> None:
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("roles")
    # `drop_table` does not cascade to a dependent enum type, so it is dropped
    # explicitly here, the same as `follow_up_policy` does after its own drop_column.
    PERMISSION.drop(op.get_bind(), checkfirst=True)
