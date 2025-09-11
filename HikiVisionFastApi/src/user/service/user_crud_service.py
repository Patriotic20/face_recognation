from core.utils.basic_service import BasicService
from fastapi import HTTPException , status
from sqlalchemy.ext.asyncio import AsyncSession
from ..schemas import UserBase 
from core.models import User 
from .user_info_service import UserInfoService
from sqlalchemy import select
from sqlalchemy.orm import joinedload

class UserCrudService:
    def __init__(self , session: AsyncSession):
        self.session = session
        self.service = BasicService(db=self.session)
        self.user_info_service = UserInfoService(session=self.session)
        
    async def create_user(self, user_data: UserBase):
        return await self.service.create(model=User , obj_items=user_data)
    
    async def get_user_by_id(self, user_id: str):
        stmt = (
            select(User)
            .options(
                joinedload(User.user_info),
                joinedload(User.role)   # load the whole Role relationship
            )
            .where(User.id == user_id)
        )
        result = await self.session.execute(stmt)
        user_data = result.scalars().first()
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user_data

        
    async def get_all_users(
        self, administration: bool, limit: int = 20, offset: int = 0
    ):
        if administration:
            condition = (User.role_id.is_not(None), User.password.is_not(None))
        else:
            condition = (User.role_id.is_(None), User.password.is_(None))

        stmt = (
            select(User)
            .options(
                joinedload(User.role)
            )
            .where(*condition)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        users = result.scalars().all()
        
        return [
            {
                "id": user.id,
                "username": user.username,
                "image_path": user.image_path,
                "role_name": user.role.name if user.role else None
            } for user in users
        ]

        
    async def update_user(self, user_id: int , user_name: str):
        return await self.service.update_by_field(item_id=user_id , model=User , field_name="username" , field_value=user_name)
    
    async def delete_user(self , user_id: str):
        await self.user_info_service.delete_user_info_by_user_id(user_id=user_id)
        return await self.service.delete(model=User , item_id=user_id)
    
