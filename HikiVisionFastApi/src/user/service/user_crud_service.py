from core.utils.basic_service import BasicService
from fastapi import HTTPException , status
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import UserBase , UserUpdate
from core.models import User
from sqlalchemy import select

class UserCrudService:
    def __init__(self , session: AsyncSession):
        self.session = session
        self.service = BasicService(db=self.session)
        
    async def create_user(self, user_data: UserBase):
        return await self.service.create(model=User , obj_items=user_data)
    
    async def get_user_by_id(self, user_id: str):
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        user_data = result.scalars().first()
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user_data
        
    async def get_all_users(self , limit: int = 20 , offset : int = 0):
        return await self.service.get_all(model=User , limit=limit , offset=offset)
    
    async def update_user(self, user_id: int , user_data: UserUpdate):
        return await self.service.update(model=User , item_id=user_id , obj_items=user_data)
    
    async def delete_user(self , user_id: str):
        return await self.service.delete(model=User , item_id=user_id)
    
