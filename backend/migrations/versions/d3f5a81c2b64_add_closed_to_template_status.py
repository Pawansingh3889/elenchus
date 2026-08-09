"""add closed to template status

Revision ID: d3f5a81c2b64
Revises: c7e1b9d40f22
Create Date: 2026-08-09 04:10:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = 'd3f5a81c2b64'
down_revision: str | None = 'c7e1b9d40f22'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # A fourth state rather than reusing archived. They read alike now and diverge exactly
    # when the dashboard is busy: archived means "hide this from my list", closed means
    # "the study is over and these numbers are final". An author closing a survey to read
    # its results should not have to hide it to do so.
    #
    # ADD VALUE runs inside Alembic's transaction, which Postgres has allowed since 12 as
    # long as the value is not also used before the commit. Nothing below uses it.
    # BEFORE 'archived' rather than appended, so the type's order matches the Python enum
    # and reads as a lifecycle: draft, published, closed, archived. Appending would leave
    # ORDER BY status sorting archived ahead of closed, which is true of nothing.
    op.execute("ALTER TYPE template_status ADD VALUE IF NOT EXISTS 'closed' BEFORE 'archived'")

    # Nullable, because most templates have never been closed and NULL says that better
    # than any sentinel date. It is the answer to "when did this stop taking answers",
    # which the dashboard shows next to the final counts.
    op.add_column(
        "survey_templates",
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("survey_templates", "closed_at")

    # Postgres cannot drop a value from an enum, so the type is rebuilt without it. Any
    # closed survey becomes archived: it is the nearest surviving meaning, both being
    # "not open", and the alternative is a downgrade that fails on exactly the rows this
    # migration was written to create.
    op.execute("ALTER TABLE survey_templates ALTER COLUMN status DROP DEFAULT")
    op.execute("UPDATE survey_templates SET status = 'archived' WHERE status = 'closed'")
    op.execute("ALTER TYPE template_status RENAME TO template_status_old")
    op.execute("CREATE TYPE template_status AS ENUM ('draft', 'published', 'archived')")
    op.execute(
        "ALTER TABLE survey_templates ALTER COLUMN status TYPE template_status "
        "USING status::text::template_status"
    )
    op.execute("ALTER TABLE survey_templates ALTER COLUMN status SET DEFAULT 'draft'")
    op.execute("DROP TYPE template_status_old")
