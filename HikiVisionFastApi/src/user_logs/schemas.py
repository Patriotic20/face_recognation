from pydantic import BaseModel , field_validator , ConfigDict , field_serializer
from datetime import datetime, timezone, timedelta
from user.schemas import UserBase

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

UTC_PLUS_5 = timezone(timedelta(hours=5))

class UserLogsResponse(BaseModel):
    id: int
    user: UserBase | None = None
    enter_time: datetime
    exit_time: datetime
    
    model_config = ConfigDict(from_attributes=True)  
    
    
    @field_serializer("enter_time", "exit_time")
    def convert_to_utc_plus_5(self, value: datetime) -> str:
        if value is None:
            return None
        return value.astimezone(UTC_PLUS_5).isoformat()
    
    
