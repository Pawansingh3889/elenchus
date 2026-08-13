"""quality department and shift managers

Revision ID: a7c4e91f5d26
Revises: f3a9c15d2b78
Create Date: 2026-08-13 13:05:00.000000

Two vocabulary additions asked for by name: a Quality department on the office side,
distinct from the QA group on the floor (the compliance people who write the hygiene
surveys are not the same people spot-checking cores on the line, though one person can
be both), and shift managers as a plant-floor group, between the line leaders and the
managers the earlier remap created.

A group only half exists without an audience to aim at it, so `survey_audience` grows in
the same breath as `respondent_group`: test_every_group_audience_maps_to_a_group is the
net that catches these two drifting apart, and it is exactly the test that fails if you
add one enum value without the other.

ADD VALUE is additive and irreversible in place: Postgres cannot drop an enum value, so
the downgrades recreate each type without the value, which only succeeds while no row
uses it. That is the honest shape of removing a vocabulary word: rows carrying it have
to be re-pointed first, and the failure names them rather than quietly unmapping them.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a7c4e91f5d26"
down_revision: str | None = "f3a9c15d2b78"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE creator_department ADD VALUE IF NOT EXISTS 'quality'")
    op.execute("ALTER TYPE respondent_group ADD VALUE IF NOT EXISTS 'shift_managers'")
    op.execute("ALTER TYPE survey_audience ADD VALUE IF NOT EXISTS 'shift_managers'")


def _drop_value(type_name: str, value: str, *columns: tuple[str, str]) -> None:
    """Recreate an enum type without one value, re-pointing the columns that use it.

    Fails, loudly and by design, if any row still holds the value: the USING cast
    refuses, and the operator is told which data to move rather than having it moved.
    """
    op.execute(f"ALTER TYPE {type_name} RENAME TO {type_name}_old")
    keep = f"""
        SELECT string_agg(quote_literal(e.enumlabel), ', ' ORDER BY e.enumsortorder)
        FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid
        WHERE t.typname = '{type_name}_old' AND e.enumlabel <> '{value}'
    """
    op.execute(
        f"DO $$ DECLARE labels text; BEGIN {keep} INTO labels; "
        f"EXECUTE format('CREATE TYPE {type_name} AS ENUM (%s)', labels); END $$"
    )
    for table, column in columns:
        # Quoted, because one of these columns is called "group" and Postgres will not
        # take that bare.
        op.execute(
            f'ALTER TABLE {table} ALTER COLUMN "{column}" '
            f'TYPE {type_name} USING "{column}"::text::{type_name}'
        )
    op.execute(f"DROP TYPE {type_name}_old")


def downgrade() -> None:
    _drop_value("survey_audience", "shift_managers", ("survey_templates", "audience"))
    _drop_value("respondent_group", "shift_managers", ("user_group_memberships", "group"))
    _drop_value("creator_department", "quality", ("users", "department"))
