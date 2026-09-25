"""fix missing audience in sample surveys

Revision ID: f2b3c4d5e6f7
Revises: e6f7a8b9c0d1
Create Date: 2026-08-23 00:45:00.000000

This migration fixes the missing audience field in existing sample surveys.
The sample surveys were created without an audience field, which caused them
to be hidden from the author dashboard due to the may_list() access rule
that rejects surveys with no audience.

We set appropriate audience values based on the survey titles and creators:
- batch-code-temperature (by arjun): managers
- factory-floor-compliance (by arjun): supervisors
- new-hire-onboarding (by arjun): everyone
- team-lead (by arjun): managers
- safety-equipment-ppe (by hana): health_safety
- shift-handover (by ava): shift_managers
- ai-tools-plant (by pawankapkoti3889): everyone
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "f2b3c4d5e6f7"
down_revision: Union[str, None] = "e6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update audience for each sample survey based on their template_id
    # These IDs match the sample data in surveys.json

    # batch-code-temperature: managers
    op.execute(
        text(
            "UPDATE survey_templates SET audience = 'managers' WHERE id = '460791a5-ca31-485c-991c-0e64762d2222'"
        )
    )

    # factory-floor-compliance: supervisors
    op.execute(
        text(
            "UPDATE survey_templates SET audience = 'supervisors' WHERE id = '00e74feb-69c7-4f85-8419-313bd1b96787'"
        )
    )

    # new-hire-onboarding: everyone
    op.execute(
        text(
            "UPDATE survey_templates SET audience = 'everyone' WHERE id = '323b17e2-aa57-416a-b87d-81da879f46ca'"
        )
    )

    # team-lead: managers
    op.execute(
        text(
            "UPDATE survey_templates SET audience = 'managers' WHERE id = '2bbabbb6-55b6-4a35-b2b9-2dddda78b46c'"
        )
    )

    # safety-equipment-ppe: health_safety
    op.execute(
        text(
            "UPDATE survey_templates SET audience = 'health_safety' WHERE id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'"
        )
    )

    # shift-handover: shift_managers
    op.execute(
        text(
            "UPDATE survey_templates SET audience = 'shift_managers' WHERE id = 'b8c9d0e1-f2a3-4567-bcde-678901234567'"
        )
    )

    # ai-tools-plant: everyone
    op.execute(
        text(
            "UPDATE survey_templates SET audience = 'everyone' WHERE id = 'deda8e62-3176-4327-8a8e-d11f2d187108'"
        )
    )

    # For any other surveys without an audience, default to 'everyone'
    op.execute(text("UPDATE survey_templates SET audience = 'everyone' WHERE audience IS NULL"))


def downgrade() -> None:
    # Set audience back to NULL for the sample surveys
    op.execute(
        text(
            "UPDATE survey_templates SET audience = NULL WHERE id IN ('460791a5-ca31-485c-991c-0e64762d2222', '00e74feb-69c7-4f85-8419-313bd1b96787', '323b17e2-aa57-416a-b87d-81da879f46ca', '2bbabbb6-55b6-4a35-b2b9-2dddda78b46c', 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'b8c9d0e1-f2a3-4567-bcde-678901234567', 'deda8e62-3176-4327-8a8e-d11f2d187108')"
        )
    )
