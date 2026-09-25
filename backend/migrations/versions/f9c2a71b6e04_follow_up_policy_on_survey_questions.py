"""follow_up_policy on survey questions

Revision ID: f9c2a71b6e04
Revises: d17c4a9e60b3
Create Date: 2026-08-10 23:58:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = 'f9c2a71b6e04'
down_revision: str | None = 'd17c4a9e60b3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FOLLOW_UP_POLICY = sa.Enum(
    "never", "when_unclear", "always_once", name="follow_up_policy"
)


def upgrade() -> None:
    bind = op.get_bind()
    FOLLOW_UP_POLICY.create(bind, checkfirst=True)

    # NOT NULL with a server default rather than nullable: "the author has no opinion on
    # probing" is not a state a question can be in, and every question already had one.
    op.add_column(
        "survey_questions",
        sa.Column(
            "follow_up_policy", FOLLOW_UP_POLICY, nullable=False, server_default="never"
        ),
    )

    # The backfill makes the column true of history rather than merely populated. A
    # question that permitted probing behaved as when_unclear, because that is exactly
    # what the old boolean bought; one that did not behaved as never. Nothing already
    # drafted changes how it is conducted.
    op.execute(
        "UPDATE survey_questions SET follow_up_policy = 'when_unclear' "
        "WHERE allow_follow_ups"
    )

    op.drop_column("survey_questions", "allow_follow_ups")


def downgrade() -> None:
    # always_once collapses back to true. The distinction it carried does not exist in a
    # boolean, and the lossy direction is the safe one: a question that always probed
    # becomes one that may probe, rather than one that never does.
    op.add_column(
        "survey_questions",
        sa.Column(
            "allow_follow_ups", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.execute(
        "UPDATE survey_questions SET allow_follow_ups = true "
        "WHERE follow_up_policy <> 'never'"
    )
    op.drop_column("survey_questions", "follow_up_policy")
    bind = op.get_bind()
    FOLLOW_UP_POLICY.drop(bind, checkfirst=True)
