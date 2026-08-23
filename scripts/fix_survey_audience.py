"""Fix missing audience field in existing sample surveys.

This script directly updates the database to fix the missing audience
field in sample surveys that was causing them to be hidden from the dashboard.
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to the path so we can import app modules
# In Docker, we're in /app which contains the backend directory
# In local dev, we're in the elenchus directory
current_dir = Path(__file__).parent.parent
if (current_dir / "app").exists():
    sys.path.insert(0, str(current_dir))
elif (current_dir / "backend" / "app").exists():
    sys.path.insert(0, str(current_dir / "backend"))

from sqlalchemy import text
from app.db.session import SessionFactory


async def fix_survey_audience() -> None:
    """Update audience field for sample surveys."""
    async with SessionFactory() as session:
        # Update audience for each sample survey based on their template_id
        updates = [
            ("460791a5-ca31-485c-991c-0e64762d2222", "managers"),  # batch-code-temperature
            ("00e74feb-69c7-4f85-8419-313bd1b96787", "supervisors"),  # factory-floor-compliance
            ("323b17e2-aa57-416a-b87d-81da879f46ca", "everyone"),  # new-hire-onboarding
            ("2bbabbb6-55b6-4a35-b2b9-2dddda78b46c", "managers"),  # team-lead
            ("a1b2c3d4-e5f6-7890-abcd-ef1234567890", "health_safety"),  # safety-equipment-ppe
            ("b8c9d0e1-f2a3-4567-bcde-678901234567", "shift_managers"),  # shift-handover
            ("deda8e62-3176-4327-8a8e-d11f2d187108", "everyone"),  # ai-tools-plant
        ]
        
        for template_id, audience in updates:
            await session.execute(
                text("UPDATE survey_templates SET audience = :audience WHERE id = :id"),
                {"audience": audience, "id": template_id}
            )
        
        # For any other surveys without an audience, default to 'everyone'
        await session.execute(
            text("UPDATE survey_templates SET audience = 'everyone' WHERE audience IS NULL")
        )
        
        await session.commit()
        print(f"Updated {len(updates)} sample surveys with audience fields")
        print("Set default audience='everyone' for any remaining surveys without audience")


if __name__ == "__main__":
    asyncio.run(fix_survey_audience())