"""add technical department

Revision ID: f1b6d38e05c4
Revises: e4a7c92b1f68
Create Date: 2026-08-09 06:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "f1b6d38e05c4"
down_revision: str | None = "e4a7c92b1f68"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Both types, because they are deliberately separate enums answering different
    # questions, and a department nobody can aim a survey at is a department that only
    # half exists. Appended rather than positioned: unlike the survey lifecycle, these
    # values are a set of teams with no meaningful order to preserve.
    #
    # ADD VALUE runs inside Alembic's transaction, which Postgres has allowed since 12 as
    # long as the value is not also used before the commit. Nothing below uses it.
    op.execute("ALTER TYPE creator_department ADD VALUE IF NOT EXISTS 'technical'")
    op.execute("ALTER TYPE survey_audience ADD VALUE IF NOT EXISTS 'technical'")


def downgrade() -> None:
    # Postgres cannot drop a value from an enum, so each type is rebuilt without it.
    # Anyone in Technical becomes operations and any survey aimed there becomes
    # respondents: the nearest surviving meaning in each case, and the alternative is a
    # downgrade that fails on precisely the rows this migration exists to allow.
    op.execute("UPDATE users SET department = 'operations' WHERE department = 'technical'")
    op.execute("ALTER TYPE creator_department RENAME TO creator_department_old")
    op.execute("CREATE TYPE creator_department AS ENUM ('admin', 'hr', 'operations', 'finance')")
    op.execute(
        "ALTER TABLE users ALTER COLUMN department TYPE creator_department "
        "USING department::text::creator_department"
    )
    op.execute("DROP TYPE creator_department_old")

    op.execute("ALTER TABLE survey_templates ALTER COLUMN audience DROP DEFAULT")
    op.execute("UPDATE survey_templates SET audience = 'respondents' WHERE audience = 'technical'")
    op.execute("ALTER TYPE survey_audience RENAME TO survey_audience_old")
    op.execute("CREATE TYPE survey_audience AS ENUM ('respondents', 'hr', 'operations', 'finance')")
    op.execute(
        "ALTER TABLE survey_templates ALTER COLUMN audience TYPE survey_audience "
        "USING audience::text::survey_audience"
    )
    op.execute("ALTER TABLE survey_templates ALTER COLUMN audience SET DEFAULT 'respondents'")
    op.execute("DROP TYPE survey_audience_old")
