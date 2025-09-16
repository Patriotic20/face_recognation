from pydantic import BaseModel , field_validator , ConfigDict , field_serializer
from datetime import datetime, timezone, timedelta
from user.schemas import UserBase

class UserLogBase(BaseModel):
    enter_time: datetime
    exit_time: datetime


class UserLogEnterCreate(BaseModel):
    user_id: str | None = None
    enter_time: datetime
    
    
class UserLogExitCreate(BaseModel):
    user_id: str | None = None
    exit_time: datetime



UTC_PLUS_5 = timezone(timedelta(hours=5))

class UserLogsResponse(BaseModel):
    id: int
    user: UserBase | None = None
    enter_time: datetime | None = None
    exit_time: datetime | None = None
    
    model_config = ConfigDict(from_attributes=True)  
    
    
    @field_serializer("enter_time", "exit_time")
    def convert_to_utc_plus_5(self, value: datetime) -> str:
        if value is None:
            return None
        return value.astimezone(UTC_PLUS_5).isoformat()
    
    
