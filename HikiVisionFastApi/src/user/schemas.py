from pydantic import BaseModel

class UserBase(BaseModel):
    username: str
    
class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    
class UserUpdate(BaseModel):
    username: str | None = None
