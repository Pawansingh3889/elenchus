"""plant groups, individual audiences, and the new creator departments

Revision ID: c7f2a91d84be
Revises: b5e9c07a3f21
Create Date: 2026-08-12 20:40:00.000000

Three vocabularies move at once, because they are one change: who a survey can be aimed
at stops being an office team and becomes what somebody does on the plant floor.

What is destroyed here, said plainly rather than discovered later. Every survey aimed at
`hr`, `operations`, `finance` or `technical` becomes `managers`. Those four values do not
survive, so the downgrade cannot put a survey back where it came from and does not
pretend to. That was decided knowingly: the alternative was carrying four dead values in
the picker forever.

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c7f2a91d84be"
down_revision: str | None = "b5e9c07a3f21"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_AUDIENCES = (
    "everyone",
    "operatives",
    "line_leaders",
    "supervisors",
    "managers",
    "qa",
    "person",
)
_OLD_AUDIENCES = ("respondents", "hr", "operations", "finance", "technical")
_NEW_DEPARTMENTS = ("hr", "finance", "technical", "management", "it")
_OLD_DEPARTMENTS = ("admin", "hr", "operations", "finance", "technical")
_GROUPS = ("operatives", "line_leaders", "supervisors", "managers", "qa")


def _rebuild_enum(
    name: str,
    values: tuple[str, ...],
    table: str,
    column: str,
    remap: dict[str, str] | None = None,
) -> None:
    """Replace a native enum type with a new set of values, remapping rows on the way.

    Postgres can add a value to an enum but not remove one, so a vocabulary that loses a
    value has to be rebuilt. The remapping has to happen *inside* the cast rather than as
    an UPDATE first: the new values do not exist in the old type, so `SET department =
    'management'` fails before the type is replaced, and `ALTER TYPE ... ADD VALUE` cannot
    be used in the same transaction that then writes the value. One statement per column
    sidesteps both, and leaves no intermediate state for a failure to strand.
    """
    cases = "".join(f" WHEN {old!r} THEN {new!r}" for old, new in (remap or {}).items())
    using = (
        f"(CASE {column}::text{cases} ELSE {column}::text END)::{name}_new"
        if cases
        else f"{column}::text::{name}_new"
    )
    op.execute(f"CREATE TYPE {name}_new AS ENUM ({', '.join(repr(v) for v in values)})")
    op.execute(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE {name}_new USING {using}")
    op.execute(f"DROP TYPE {name}")
    op.execute(f"ALTER TYPE {name}_new RENAME TO {name}")


def upgrade() -> None:
    # The old administration department becomes Management rather than IT. IT now grants
    # admin, and quietly promoting whoever happened to sit in the `admin` department is
    # not a migration's decision to make.
    _rebuild_enum(
        "creator_department",
        _NEW_DEPARTMENTS,
        "users",
        "department",
        {"operations": "management", "admin": "management"},
    )

    # The audience column carries a server default, and a default referencing the old type
    # blocks the swap. Dropped here, restored at the end pointing at the new vocabulary.
    op.execute("ALTER TABLE survey_templates ALTER COLUMN audience DROP DEFAULT")
    _rebuild_enum(
        "survey_audience",
        _NEW_AUDIENCES,
        "survey_templates",
        "audience",
        {
            "respondents": "everyone",
            "hr": "managers",
            "operations": "managers",
            "finance": "managers",
            "technical": "managers",
        },
    )
    op.execute("ALTER TABLE survey_templates ALTER COLUMN audience SET DEFAULT 'everyone'")

    op.add_column(
        "survey_templates",
        sa.Column("audience_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_survey_templates_audience_user_id_users",
        "survey_templates",
        "users",
        ["audience_user_id"],
        ["id"],
    )
    op.create_index(
        "ix_survey_templates_audience_user_id", "survey_templates", ["audience_user_id"]
    )
    # The pairing rule in the database as well as in the schema. The service already
    # refuses both halves, and this is what stops a hand-written UPDATE creating a survey
    # aimed at a person it does not name.
    #
    # Named bare, not `ck_survey_templates_...`: the metadata naming convention in
    # app/db/base.py already prefixes `ck_%(table_name)s_`, and passing the prefix here
    # too produced `ck_survey_templates_ck_survey_templates_person_names_someone`, which
    # the downgrade then could not find.
    op.create_check_constraint(
        "person_names_someone",
        "survey_templates",
        "(audience = 'person') = (audience_user_id IS NOT NULL)",
    )

    group_enum = postgresql.ENUM(*_GROUPS, name="respondent_group", create_type=False)
    group_enum.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "user_group_memberships",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group", group_enum, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        # The pair is the key, so the same person cannot be recorded in one group twice.
        sa.PrimaryKeyConstraint("user_id", "group"),
    )


def downgrade() -> None:
    op.drop_table("user_group_memberships")
    op.execute("DROP TYPE respondent_group")

    op.drop_constraint("ck_survey_templates_person_names_someone", "survey_templates")
    op.drop_index("ix_survey_templates_audience_user_id", table_name="survey_templates")
    op.drop_constraint(
        "fk_survey_templates_audience_user_id_users", "survey_templates", type_="foreignkey"
    )
    op.drop_column("survey_templates", "audience_user_id")

    # Everything lands on `respondents`, which is the only honest destination. The four
    # office-team values were collapsed into `managers` on the way up and there is nothing
    # left in the row to tell them apart again, so this does not guess.
    op.execute("ALTER TABLE survey_templates ALTER COLUMN audience DROP DEFAULT")
    _rebuild_enum(
        "survey_audience",
        _OLD_AUDIENCES,
        "survey_templates",
        "audience",
        {value: "respondents" for value in _NEW_AUDIENCES},
    )
    op.execute("ALTER TABLE survey_templates ALTER COLUMN audience SET DEFAULT 'respondents'")

    _rebuild_enum(
        "creator_department",
        _OLD_DEPARTMENTS,
        "users",
        "department",
        {"management": "operations", "it": "admin"},
    )
