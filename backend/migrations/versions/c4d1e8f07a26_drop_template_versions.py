"""Drop published versions; a run points at the survey itself.

Removes the immutable snapshot taken at publish time. What that property bought is
worth naming, because this migration is where it is given up: a published survey could
not change under the people answering it, and every answer could be read back against
the exact wording it was given. From here, editing a published survey changes the
question that earlier answers were given to, and the only record of the original wording
is the ``question_text`` each answer already carries on its own row.

Asked for directly on 16 Aug 2026. See CLAUDE.md for the decision and its cost.

`survey_runs.template_version_id` becomes `template_id`. Written as drop-and-add rather
than as a data migration because the table was emptied first: carrying the old column
across would mean resolving every run to whichever template its version belonged to, and
there were no rows left to resolve.

Revision ID: c4d1e8f07a26
Revises: b2e7f43a9c15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4d1e8f07a26"
down_revision: str | Sequence[str] | None = "b2e7f43a9c15"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # The template gains what the version used to record. Publishing is now a status
    # change, and "when, and by whom" is worth keeping even without a snapshot to hang
    # it on: it is the first thing anyone asks of a survey that produced surprising
    # answers.
    op.add_column(
        "survey_templates",
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "survey_templates",
        sa.Column("published_by", sa.UUID(), sa.ForeignKey("users.id"), nullable=True),
    )

    op.drop_constraint("fk_survey_runs_template_version_id_survey_template_versions", "survey_runs")
    op.drop_column("survey_runs", "template_version_id")
    op.add_column(
        "survey_runs",
        sa.Column("template_id", sa.UUID(), nullable=False),
    )
    op.create_foreign_key(
        "fk_survey_runs_template_id_survey_templates",
        "survey_runs",
        "survey_templates",
        ["template_id"],
        ["id"],
    )
    op.create_index("ix_survey_runs_template_id", "survey_runs", ["template_id"])

    op.drop_table("survey_template_versions")


def downgrade() -> None:
    """Rebuilds the table and the column, and cannot rebuild the snapshots.

    A downgrade restores the shape, not the history: the frozen definitions are gone,
    and nothing here can reconstruct what a question said at the moment somebody
    answered it. Stated rather than silently implied, because a downgrade that looks
    complete and is not is worse than one that refuses.
    """
    op.create_table(
        "survey_template_versions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "template_id", sa.UUID(), sa.ForeignKey("survey_templates.id"), nullable=False
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("definition", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("published_by", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.UniqueConstraint("template_id", "version", name="version_template_version"),
    )
    op.drop_index("ix_survey_runs_template_id", "survey_runs")
    op.drop_constraint("fk_survey_runs_template_id_survey_templates", "survey_runs")
    op.drop_column("survey_runs", "template_id")
    op.add_column(
        "survey_runs",
        sa.Column("template_version_id", sa.UUID(), nullable=False),
    )
    op.create_foreign_key(
        "fk_survey_runs_template_version_id_survey_template_versions",
        "survey_runs",
        "survey_template_versions",
        ["template_version_id"],
        ["id"],
    )
    op.drop_column("survey_templates", "published_by")
    op.drop_column("survey_templates", "published_at")
