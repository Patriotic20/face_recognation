from pydantic import BaseModel


class UserBase(BaseModel):
    id:str
    username: str
    image_path: str
    
    
class UserCreate(BaseModel):
    username: str
    image_path: str
    
    
class UserUpdate(BaseModel):
    id: str | None = None
    username: str | None = None
    

