from core.utils.basic_service import BasicService
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import UserLog
from .schemas import UserLogEnterCreate 
from datetime import datetime
from sqlalchemy import select , desc
from sqlalchemy.orm import joinedload


class UserLogService:
    def __init__(self , session:AsyncSession):
        self.session = session
        self.service = BasicService(db=self.session)
    
    async def create_user_logs(self, user_log_create: UserLogEnterCreate):
        stmt = (
            select(UserLog)
            .where(
                UserLog.user_id == user_log_create.user_id,
                UserLog.exit_time.is_(None)  # unfinished log
            )
            .order_by(desc(UserLog.enter_time))  # latest unfinished entry
            .limit(1)
        )
        
        result = await self.session.execute(stmt)
        user_log_data = result.scalars().first()
        
        if user_log_data:
            return {"message": "You haven't exited yet, so you can't enter again."}
            
        return await self.service.create(model=UserLog, obj_items=user_log_create)

    
    async def get_user_logs_by_id(self,  user_log_id: int):
        return await self.service.get_by_id(model=UserLog , item_id=user_log_id)
    
    async def get_user_logs_by_user_id(self , user_id: int):
        return await self.service.get_by_field(model=UserLog , field_name="user_id" , field_value=user_id)
    
    async def get_all_user_logs(
        self,
        limit: int = 10,
        offset: int = 0
        ):
        stmt = (
            select(UserLog)
            .options(
                joinedload(UserLog.user)
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
        
    async def update_user_logs(self, user_id: str, field_name: str ,field_value: any):
        return await self.service.update_by_field(model=UserLog, user_id=user_id , field_name=field_name , field_value=field_value)
    
    async def update_user_log_exit_time(self, user_id: str, exit_time: datetime):
        stmt = (
            select(UserLog)
            .where(
                UserLog.user_id == user_id,
                UserLog.exit_time.is_(None)
            )
            .order_by(desc(UserLog.enter_time))  
            .limit(1)
        )

        result = await self.session.execute(stmt)
        user_log_data = result.scalars().first()

        if user_log_data:
            user_log_data.exit_time = exit_time
            await self.session.commit()
            return user_log_data
        else:
            return {"message": "You haven't entered, so you cannot exit."}

    async def delete_user_logs(self):
        pass
