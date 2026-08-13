"""one job per person: function and band replace role, department and groups

Revision ID: b2e7f43a9c15
Revises: a7c4e91f5d26
Create Date: 2026-08-13 15:20:00.000000

The vocabulary swap behind the job model. `users.role`, `users.department` and the
`user_group_memberships` table collapse into `users.function` + `users.band` plus a
small `user_hats` table, and the survey audience gains `health_safety`. The old shape
could record a line leader who was also QA, a job the plant's own org chart does not
contain; one (function, band) pair per person makes that unrepresentable.

The remap runs in two passes. The seeded cast is mapped by email to the jobs the new
seed constant gives them, because the generic rules cannot know that Ava is a shift
manager rather than an office manager. Everyone else is mapped by deterministic rules:
authors take their department's function at manager band, respondents take the highest
plant group they held. Rows with no role and no groups stay job-less, which is what a
service account is. Audit rows in account_changes are deliberately untouched: they are
history, and they keep the vocabulary they were written in.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b2e7f43a9c15"
down_revision: str | None = "a7c4e91f5d26"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USER_FUNCTION = sa.Enum(
    "production",
    "quality",
    "health_safety",
    "technical",
    "planning",
    "hr",
    "finance",
    "supply_chain",
    "it",
    "executive",
    name="user_function",
)
USER_BAND = sa.Enum(
    "operative",
    "line_leader",
    "supervisor",
    "manager",
    "head",
    "director",
    name="user_band",
)
USER_HAT = sa.Enum("health_safety", name="user_hat")

# The seeded cast, by email, with the jobs app/seed.py now records for them. By email
# rather than id for the same reason the seed guards ids by email: an id occupied by a
# stranger must not inherit a seed user's job.
#
# Adaeze is deliberately absent. The seed gives her executive/head on a fresh checkout,
# but a migrated database may hold her in IT, which is a local admin grant somebody made
# on purpose; the generic department rule below maps it to the IT function and keeps
# that grant, where the seed job would silently revoke it.
SEED_JOBS: dict[str, tuple[str, str]] = {
    "ava@elenchus.dev": ("production", "manager"),
    "arjun@elenchus.dev": ("hr", "manager"),
    "fatima@elenchus.dev": ("finance", "manager"),
    "tomas@elenchus.dev": ("quality", "head"),
    "quinn@elenchus.dev": ("quality", "manager"),
    "rosa@elenchus.dev": ("production", "operative"),
    "ravi@elenchus.dev": ("production", "line_leader"),
    "remy@elenchus.dev": ("production", "operative"),
    "rina@elenchus.dev": ("production", "manager"),
    "rohan@elenchus.dev": ("production", "supervisor"),
}

# One department, one function; management's members become executive because that
# department was already the catch-all for site leadership.
DEPARTMENT_FUNCTION: dict[str, str] = {
    "hr": "hr",
    "finance": "finance",
    "technical": "technical",
    "quality": "quality",
    "management": "executive",
    "it": "it",
}

# Highest group wins, so somebody the old table held in two groups lands on the more
# senior job. qa maps to the quality floor because the seniors of that ladder held
# author accounts and are caught by the department rule first.
GROUP_JOBS: list[tuple[str, str, str]] = [
    ("shift_managers", "production", "manager"),
    ("managers", "production", "manager"),
    ("supervisors", "production", "supervisor"),
    ("line_leaders", "production", "line_leader"),
    ("qa", "quality", "operative"),
    ("operatives", "production", "operative"),
]


def upgrade() -> None:
    bind = op.get_bind()
    USER_FUNCTION.create(bind, checkfirst=True)
    USER_BAND.create(bind, checkfirst=True)
    USER_HAT.create(bind, checkfirst=True)

    op.add_column("users", sa.Column("function", USER_FUNCTION, nullable=True))
    op.add_column("users", sa.Column("band", USER_BAND, nullable=True))

    # Every bound parameter that lands in an enum column is cast explicitly: asyncpg
    # sends them as varchar, and Postgres refuses varchar-into-enum without the cast.
    for email, (function, band) in SEED_JOBS.items():
        op.execute(
            sa.text(
                "UPDATE users SET function = CAST(:function AS user_function), "
                "band = CAST(:band AS user_band) WHERE email = :email"
            ).bindparams(function=function, band=band, email=email)
        )

    for department, function in DEPARTMENT_FUNCTION.items():
        op.execute(
            sa.text(
                "UPDATE users SET function = CAST(:function AS user_function), "
                "band = 'manager' "
                "WHERE function IS NULL AND role = 'author' "
                "AND department = CAST(:department AS creator_department)"
            ).bindparams(function=function, department=department)
        )

    for group, function, band in GROUP_JOBS:
        op.execute(
            sa.text(
                "UPDATE users SET function = CAST(:function AS user_function), "
                "band = CAST(:band AS user_band) "
                "WHERE function IS NULL AND id IN "
                "(SELECT user_id FROM user_group_memberships "
                ' WHERE "group" = CAST(:grp AS respondent_group))'
            ).bindparams(function=function, band=band, grp=group)
        )

    op.create_table(
        "user_hats",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        # create_type=False: the type was created above, and create_table would
        # otherwise issue a second CREATE TYPE in the same transaction and abort it.
        sa.Column(
            "hat",
            postgresql.ENUM("health_safety", name="user_hat", create_type=False),
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    # Rohan's H&S duty, the one hat the retired data implies: the seed records him as a
    # supervisor with additional health and safety responsibility.
    op.execute(
        "INSERT INTO user_hats (user_id, hat) "
        "SELECT id, 'health_safety' FROM users WHERE email = 'rohan@elenchus.dev' "
        "ON CONFLICT DO NOTHING"
    )

    op.create_check_constraint(
        "ck_users_job_is_both_or_neither",
        "users",
        "(function IS NULL) = (band IS NULL)",
    )

    op.drop_table("user_group_memberships")
    op.drop_column("users", "role")
    op.drop_column("users", "department")
    sa.Enum(name="respondent_group").drop(bind, checkfirst=True)
    sa.Enum(name="user_role").drop(bind, checkfirst=True)
    sa.Enum(name="creator_department").drop(bind, checkfirst=True)

    # Since PostgreSQL 12 ADD VALUE may run inside a transaction, as long as the new
    # value is not also used in it; this migration only adds it.
    op.execute("ALTER TYPE survey_audience ADD VALUE IF NOT EXISTS 'health_safety' BEFORE 'person'")


def downgrade() -> None:
    """Best effort, and lossy where the old shape was poorer than the new.

    A hat has no membership equivalent, planning and supply_chain had no department,
    and one band collapses back into a coarse role. The reverse mapping exists so a
    checkout can walk back for a bisect, not because the round trip preserves data.
    """
    bind = op.get_bind()

    sa.Enum(
        "hr", "finance", "technical", "management", "quality", "it", name="creator_department"
    ).create(bind, checkfirst=True)
    sa.Enum("author", "respondent", name="user_role").create(bind, checkfirst=True)
    respondent_group = sa.Enum(
        "operatives",
        "line_leaders",
        "supervisors",
        "shift_managers",
        "managers",
        "qa",
        name="respondent_group",
    )
    respondent_group.create(bind, checkfirst=True)

    op.add_column(
        "users",
        sa.Column("department", sa.Enum(name="creator_department"), nullable=True),
    )
    op.add_column("users", sa.Column("role", sa.Enum(name="user_role"), nullable=True))
    op.execute(
        "UPDATE users SET role = CASE "
        "WHEN band IN ('manager', 'head', 'director') THEN 'author'::user_role "
        "ELSE 'respondent'::user_role END"
    )
    op.execute("UPDATE users SET role = 'respondent' WHERE role IS NULL")
    op.alter_column("users", "role", nullable=False)
    for department, function in DEPARTMENT_FUNCTION.items():
        op.execute(
            sa.text(
                "UPDATE users SET department = CAST(:department AS creator_department) "
                "WHERE role = 'author' AND function = CAST(:function AS user_function)"
            ).bindparams(department=department, function=function)
        )
    op.execute(
        "UPDATE users SET department = 'management' WHERE role = 'author' AND department IS NULL"
    )

    op.create_table(
        "user_group_memberships",
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "group",
            postgresql.ENUM(
                "operatives",
                "line_leaders",
                "supervisors",
                "shift_managers",
                "managers",
                "qa",
                name="respondent_group",
                create_type=False,
            ),
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    for group, function, band in [
        ("operatives", "production", "operative"),
        ("line_leaders", "production", "line_leader"),
        ("supervisors", "production", "supervisor"),
        ("shift_managers", "production", "manager"),
        ("qa", "quality", "operative"),
    ]:
        op.execute(
            sa.text(
                'INSERT INTO user_group_memberships (user_id, "group") '
                "SELECT id, CAST(:grp AS respondent_group) FROM users "
                "WHERE function = CAST(:function AS user_function) "
                "AND band = CAST(:band AS user_band) "
                "ON CONFLICT DO NOTHING"
            ).bindparams(grp=group, function=function, band=band)
        )

    op.drop_constraint("ck_users_job_is_both_or_neither", "users")
    op.drop_table("user_hats")
    op.drop_column("users", "band")
    op.drop_column("users", "function")
    sa.Enum(name="user_hat").drop(bind, checkfirst=True)
    sa.Enum(name="user_band").drop(bind, checkfirst=True)
    sa.Enum(name="user_function").drop(bind, checkfirst=True)
    # The health_safety audience value stays: PostgreSQL cannot remove an enum value,
    # and a survey aimed at it, should one exist, is data this downgrade must not eat.
