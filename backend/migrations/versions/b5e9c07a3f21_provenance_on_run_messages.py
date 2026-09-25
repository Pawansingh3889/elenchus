"""provenance on run messages

Revision ID: b5e9c07a3f21
Revises: a3d81f5c2e97
Create Date: 2026-08-12 05:20:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = 'b5e9c07a3f21'
down_revision: str | None = 'a3d81f5c2e97'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nullable with no server default, and deliberately no backfill, which is the
    # opposite of the choice `language` made one migration over. The difference is
    # whether a default would be *true*: every existing run really was conducted in
    # English, but no existing message is known to have come from today's prompt version
    # or today's model. Stamping one on would manufacture a provenance record that reads
    # exactly like a measured one, and the first question anybody asks of this column
    # ("which version produced this?") would get a confident wrong answer.
    #
    # Null therefore means "written before anyone recorded this", and stays legible as
    # that forever. A respondent's own message is null too: they produced it themselves.
    op.add_column("run_messages", sa.Column("prompt_version", sa.String(length=64), nullable=True))
    op.add_column("run_messages", sa.Column("model", sa.String(length=128), nullable=True))
    op.add_column("run_messages", sa.Column("tier", sa.SmallInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("run_messages", "tier")
    op.drop_column("run_messages", "model")
    op.drop_column("run_messages", "prompt_version")
