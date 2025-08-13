from pydantic import BaseModel 
from datetime import datetime 

    
class EnterEvent(BaseModel):
    user_id: str | None = None
    time: datetime | None = None
    camera_type: str

    

