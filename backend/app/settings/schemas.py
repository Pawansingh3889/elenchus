from pydantic import BaseModel, Field


class TierConfig(BaseModel):
    enabled: bool | None = None
    timeout_seconds: float | None = Field(None, gt=0)
    prompt_cache: bool | None = None
    max_completion_tokens: int | None = Field(None, gt=0)


class SettingsRead(BaseModel):
    tier_config: dict[str, TierConfig]


class SettingsUpdate(BaseModel):
    tier_config: dict[str, TierConfig]
