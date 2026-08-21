"""unit and display_unit on survey_questions

Revision ID: f1a2b3c4d5e6
Revises: e6f7a8b9c0d1
Create Date: 2026-08-21 11:00:00.000000

A measured answer is meaningless without its unit: the temperature question that had
none is the case. ``unit`` is what the number is in; ``display_unit`` is an optional
second unit the respondent (and the results) also see, e.g. °C with °F. Both nullable
because most questions are not measured quantities, and currency is deliberately absent
(app/units.py explains why). Plain nullable strings: the allowed vocabulary is enforced
in the schema, not here.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "e6f7a8b9c0d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("survey_questions", sa.Column("unit", sa.String(), nullable=True))
    op.add_column("survey_questions", sa.Column("display_unit", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("survey_questions", "display_unit")
    op.drop_column("survey_questions", "unit")
