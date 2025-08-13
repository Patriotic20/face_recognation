from pydantic import BaseModel , field_validator
from datetime import datetime, timezone, timedelta

class UserLogBase(BaseModel):
    enter_time: datetime
    exit_time: datetime

tz_plus_8 = timezone(timedelta(hours=8))

class UserLogEnterCreate(BaseModel):
    user_id: str | None = None
    enter_time: datetime

    @field_validator("enter_time", mode="before")
    def ensure_tz_plus_8(cls, value):
        if isinstance(value, datetime):
            if value.tzinfo is None:
                # Add +08 timezone if missing
                return value.replace(tzinfo=tz_plus_8)
            return value.astimezone(tz_plus_8)
        return value
