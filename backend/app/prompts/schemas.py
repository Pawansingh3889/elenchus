"""What the prompt admin screen reads and sends."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PromptVersionRead(BaseModel):
    name: str
    source: Literal["file", "database"]
    active: bool
    created_at: datetime | None
    created_by_name: str | None
    note: str | None
    # From the trace. None means no traced turn ran under it, which includes every turn
    # before spans existed; it is not a claim the version was never used.
    turns: int | None
    runs: int | None
    turn_ms_p50: float | None
    cost_usd: float | None


class PromptFamilyRead(BaseModel):
    family: str
    active: str
    # The version the code names, which is live whenever nobody has activated another.
    default: str
    versions: list[PromptVersionRead]


class PromptBodyRead(BaseModel):
    name: str
    source: Literal["file", "database"]
    body: str


class PromptVersionWrite(BaseModel):
    body: str = Field(min_length=1, max_length=40_000)
    note: str | None = Field(default=None, max_length=500)


class PromptActivate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
