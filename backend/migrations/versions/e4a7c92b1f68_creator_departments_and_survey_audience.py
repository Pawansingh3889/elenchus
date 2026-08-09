"""creator departments and survey audience

Revision ID: e4a7c92b1f68
Revises: d3f5a81c2b64
Create Date: 2026-08-09 05:10:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = 'e4a7c92b1f68'
down_revision: str | None = 'd3f5a81c2b64'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CREATOR_DEPARTMENT = sa.Enum(
    "admin", "hr", "operations", "finance", name="creator_department"
)
SURVEY_AUDIENCE = sa.Enum(
    "respondents", "hr", "operations", "finance", name="survey_audience"
)


def upgrade() -> None:
    bind = op.get_bind()
    CREATOR_DEPARTMENT.create(bind, checkfirst=True)
    SURVEY_AUDIENCE.create(bind, checkfirst=True)

    # Nullable, because a respondent has no department and never will: they are one pool,
    # and the site attributes planned for them are a different mechanism. A creator with
    # NULL is a misconfiguration rather than a state, and access fails closed on it.
    op.add_column("users", sa.Column("department", CREATOR_DEPARTMENT, nullable=True))

    # Existing creators become operations, as agreed. This is an access decision made on
    # everyone's behalf, so it is deliberately narrow: only rows that are already authors,
    # never respondents, and it names the role rather than assuming the table holds one
    # kind of user.
    op.execute("UPDATE users SET department = 'operations' WHERE role = 'author'")

    # NOT NULL with a server default rather than nullable: a survey aimed at nobody is not
    # a state it can be in. The default backfills every existing survey to the respondent
    # pool, which is exactly what they were, so the column is true of history rather than
    # merely populated and nothing already published changes reach.
    op.add_column(
        "survey_templates",
        sa.Column("audience", SURVEY_AUDIENCE, nullable=False, server_default="respondents"),
    )


def downgrade() -> None:
    op.drop_column("survey_templates", "audience")
    op.drop_column("users", "department")
    bind = op.get_bind()
    SURVEY_AUDIENCE.drop(bind, checkfirst=True)
    CREATOR_DEPARTMENT.drop(bind, checkfirst=True)
