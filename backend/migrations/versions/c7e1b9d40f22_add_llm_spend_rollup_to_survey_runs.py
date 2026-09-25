"""add llm spend rollup to survey runs

Revision ID: c7e1b9d40f22
Revises: a1c4d2e7f930
Create Date: 2026-08-07 00:30:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "c7e1b9d40f22"
down_revision: str | None = "a1c4d2e7f930"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # NOT NULL with a zero default. Existing runs really did spend tokens, and this
    # backfills them to zero rather than to their true cost, which nothing recorded at
    # the time. Zero is the honest value for "nothing was measured": the alternative is
    # nullable columns where every later sum has to decide what a NULL means.
    #
    # Numeric rather than double precision for the money column. It is summed across runs
    # to answer what a batch of interviews cost, and binary floating point drifts over a
    # few thousand additions. 8 decimal places is set by the small end, not the large: a
    # single 30-second local call is fractions of a cent.
    op.add_column(
        "survey_runs",
        sa.Column("llm_calls", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "survey_runs",
        sa.Column("llm_prompt_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "survey_runs",
        sa.Column(
            "llm_completion_tokens", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
    )
    # Calls whose tokens or cost the provider never reported, so a total can say "at
    # least" instead of quietly conflating unknown with zero.
    op.add_column(
        "survey_runs",
        sa.Column("llm_unmetered_calls", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "survey_runs",
        sa.Column("llm_cost_usd", sa.Numeric(18, 8), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    op.drop_column("survey_runs", "llm_cost_usd")
    op.drop_column("survey_runs", "llm_unmetered_calls")
    op.drop_column("survey_runs", "llm_completion_tokens")
    op.drop_column("survey_runs", "llm_prompt_tokens")
    op.drop_column("survey_runs", "llm_calls")
