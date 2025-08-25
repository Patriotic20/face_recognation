from pydantic import BaseModel



class UserBase(BaseModel):
    id:str
    username: str
    image_path: str | None
    
    
class UserInfoBase(BaseModel):
    first_name: str | None = None 
    last_name: str | None = None
    third_name: str | None = None
    passport_serial: str | None = None
    department: str | None = None
    
    
    
class UserMe(UserBase):
    role: str | None = None
    user_info: UserInfoBase | None = None
    
    

    
class UserCreate(BaseModel):
    username: str
    image_path: str
    first_name: str | None = None 
    last_name: str | None = None
    third_name: str | None = None
    passport_serial: str | None = None
    department: str | None = None
    
    
class UserUpdate(BaseModel):
    id: str | None = None
    username: str | None = None
    





class UserInfoCreate(UserInfoBase):
    user_id: str
    
    
    

