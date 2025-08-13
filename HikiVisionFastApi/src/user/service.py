from core.utils.basic_service import BasicService
from core.utils.db_helper import session
from core.models import User

from .schemas import UserCreate , UserUpdate , UserResponse

class UserService:
    def __init__(self):
        self.service = BasicService(session)
    
    async def create_user(self , username: UserCreate) -> UserResponse:
        return await self.service.create(model=User , obj_items=username)

    async def get_user_by_id(self , user_id: int) -> UserResponse:
        return await self.service.get_by_id(model=User , item_id=user_id)
    
    async def get_all_users(self , limit: int , offset: int ) -> list[UserResponse]:
        return await self.service.get_all(model=User ,limit=limit , offset=offset)
    
    async def update_user(self , user_id: int , username:UserUpdate)-> UserResponse:
        return await self.service.update(model=User , item_id=user_id , obj_items=username)
    
    async def delete_user(self, user_id: int):
        await self.service.delete(model=User , item_id=user_id)
        return {"message": "Successful deletion by the user"}
