from datetime import datetime, timezone
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class Fragment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    session_id: UUID
    started_at: datetime
    ended_at: datetime
    timezone: str
    text: str = Field(min_length=1, max_length=24000)
    source: Literal["phone_microphone", "watch_import", "synthetic_demo"]
    asr_engine: str = Field(min_length=1, max_length=120)
    language: str = Field(default="zh", max_length=24)
    # Permission to publish is an explicit session choice, never inferred from text.
    publish_to_dot: bool = False

    @field_validator("started_at", "ended_at")
    @classmethod
    def aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Timestamp must contain a timezone offset")
        try:
            return value.astimezone(timezone.utc)
        except OverflowError:
            raise ValueError("Timestamp must be representable in UTC") from None

    @field_validator("timezone")
    @classmethod
    def zone_exists(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Use a valid IANA timezone") from None
        return value

    @field_validator("text")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Transcript cannot contain only whitespace")
        return value

    @model_validator(mode="after")
    def interval(self):
        seconds = (self.ended_at - self.started_at).total_seconds()
        if not 0 < seconds <= 1800:
            raise ValueError("Fragment duration must be in (0, 1800] seconds")
        return self
