from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete , select, and_
from fastapi import HTTPException , status

from core.utils.basic_service import BasicService
from core.models.user_info import UserInfo
from user.schemas import UserInfoBase , UserInfoCreate



class UserInfoService:
    def __init__(self , session: AsyncSession):
        self.session = session
        self.service = BasicService(db=self.session)
    
    async def create_user_info(self, user_info_data: UserInfoCreate):
        return await self.service.create(model=UserInfo , obj_items=user_info_data)
    
    async def get_user_info_by_id(self , user_info_id: int):
        return await self.service.get_by_id(model=UserInfo , item_id=user_info_id)
        
    async def get_all_user_info(self , limit: int = 20, offset: int = 0):
        stmt = (
            select(UserInfo)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_user_info(
        self, 
        user_info_data: UserInfoBase,
        user_info_id: int | None = None , 
        user_id: str | None = None,
        ):
        return await self.service.update(
            model=UserInfo, 
            item_id=user_info_id,
            user_id=user_id, 
            obj_items=user_info_data
            )

    
        
    async def delete_user_info_by_id(self, user_info_id: int):
        return await self.service.delete(model=UserInfo , item_id=user_info_id)

    async def delete_user_info_by_user_id(self, user_id: str) -> int:
        stmt = delete(UserInfo).where(UserInfo.user_id == user_id)
        await self.session.execute(stmt)
        await self.session.commit()
        return {"message": f"Deleted successfully by id {user_id}"}
        
