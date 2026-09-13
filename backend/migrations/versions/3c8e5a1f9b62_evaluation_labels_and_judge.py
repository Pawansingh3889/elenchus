"""evaluation labels and judge

Revision ID: 3c8e5a1f9b62
Revises: 8e4b2d6f1a37
Create Date: 2026-09-13 20:00:00.000000

People's labels on recorded answers, in the database and on the committed corpus, and a
judge model's verdicts grouped by the judging that produced them. The verdict enum is
created once and shared by both label tables.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "3c8e5a1f9b62"
down_revision: str | None = "8e4b2d6f1a37"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LABEL_VERDICT = postgresql.ENUM(
    "supported", "invented", "unsure", name="label_verdict", create_type=False
)


def upgrade() -> None:
    LABEL_VERDICT.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "answer_labels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("answer_id", sa.Uuid(), nullable=False),
        sa.Column("verdict", LABEL_VERDICT, nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("labelled_by", sa.Uuid(), nullable=False),
        sa.Column("labelled_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["answer_id"],
            ["answers.id"],
            name=op.f("fk_answer_labels_answer_id_answers"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["labelled_by"], ["users.id"], name=op.f("fk_answer_labels_labelled_by_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_answer_labels")),
        sa.UniqueConstraint("answer_id", name=op.f("uq_answer_labels_answer_id")),
    )
    op.create_table(
        "corpus_labels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("fixture", sa.String(length=128), nullable=False),
        sa.Column("answer_index", sa.Integer(), nullable=False),
        sa.Column("verdict", LABEL_VERDICT, nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("labelled_by", sa.Uuid(), nullable=False),
        sa.Column("labelled_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["labelled_by"], ["users.id"], name=op.f("fk_corpus_labels_labelled_by_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_corpus_labels")),
        sa.UniqueConstraint("fixture", "answer_index", name="uq_corpus_labels_fixture_answer"),
    )
    op.create_table(
        "judge_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("tier", sa.SmallInteger(), nullable=True),
        sa.Column("answers", sa.Integer(), nullable=False),
        sa.Column("flagged", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(precision=14, scale=8), nullable=False),
        sa.Column("unmetered_calls", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("judged_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["survey_runs.id"],
            name=op.f("fk_judge_runs_run_id_survey_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_judge_runs")),
    )
    op.create_index(op.f("ix_judge_runs_run_id"), "judge_runs", ["run_id"])
    op.create_table(
        "judge_verdicts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("judge_run_id", sa.Uuid(), nullable=False),
        sa.Column("answer_id", sa.Uuid(), nullable=False),
        sa.Column("supported", sa.Boolean(), nullable=False),
        sa.Column("why", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["judge_run_id"],
            ["judge_runs.id"],
            name=op.f("fk_judge_verdicts_judge_run_id_judge_runs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["answer_id"],
            ["answers.id"],
            name=op.f("fk_judge_verdicts_answer_id_answers"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_judge_verdicts")),
        sa.UniqueConstraint("judge_run_id", "answer_id", name="uq_judge_verdicts_run_answer"),
    )
    op.create_index(op.f("ix_judge_verdicts_judge_run_id"), "judge_verdicts", ["judge_run_id"])
    op.create_index(op.f("ix_judge_verdicts_answer_id"), "judge_verdicts", ["answer_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_judge_verdicts_answer_id"), table_name="judge_verdicts")
    op.drop_index(op.f("ix_judge_verdicts_judge_run_id"), table_name="judge_verdicts")
    op.drop_table("judge_verdicts")
    op.drop_index(op.f("ix_judge_runs_run_id"), table_name="judge_runs")
    op.drop_table("judge_runs")
    op.drop_table("corpus_labels")
    op.drop_table("answer_labels")
    LABEL_VERDICT.drop(op.get_bind(), checkfirst=True)
