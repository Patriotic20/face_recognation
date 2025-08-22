from pydantic import BaseModel , field_validator
from fastapi import Form

class UserCredentials(BaseModel):
    username: str
    password: str

    @classmethod
    def as_form(
        cls,
        username: str = Form(...),
        password: str = Form(...),
    ):
        return cls(username=username, password=password)


class TokenData(BaseModel):
    username: str
    role: str
    
    
class UserRegister(BaseModel):
    username: str
    password: str
    role_name: str
    
class UserCreate(UserCredentials):
    id: str
    username: str
    password: str
    role_id: int
    
