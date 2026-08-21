"""Runtime application settings, stored in the database.

A singleton row that lets an administrator override LLM tier parameters
without restarting the process. Every tier has the same shape; fields absent
from the stored dict fall back to the values loaded from the environment at
startup.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default="singleton")
    tier_config: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
