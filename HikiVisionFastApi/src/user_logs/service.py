from datetime import datetime
from sqlalchemy import select , desc
from sqlalchemy.orm import joinedload , selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from openpyxl import Workbook
from io import BytesIO

from core.utils.basic_service import BasicService
from core.models import UserLog , UserInfo , User
from .schemas import UserLogEnterCreate 



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
    
    
    async def make_exel_file(self) -> BytesIO:
        stmt = (
            select(User)
            .options(
                selectinload(User.user_info),
                selectinload(User.user_logs),
            )
        )
        result = await self.session.execute(stmt)
        users = result.scalars().all()

        wb = Workbook()
        ws = wb.active
        ws.title = "Users"

        header = [
            "First_name",
            "Last_name",
            "Third_name",
            "Passport_serial",
            "Department",
            "Enter_time",
            "Exit_time",
        ]
        ws.append(header)

        for user in users:
            info = user.user_info
            if not info:
                continue
            if user.user_logs:
                for log in user.user_logs:
                    ws.append([
                        info.first_name,
                        info.last_name,
                        info.third_name,
                        info.passport_serial,
                        info.department,
                        log.enter_time.strftime("%Y-%m-%d %H:%M:%S") if log.enter_time else None,
                        log.exit_time.strftime("%Y-%m-%d %H:%M:%S") if log.exit_time else None,
                    ])
            else:
                ws.append([
                    info.first_name,
                    info.last_name,
                    info.third_name,
                    info.passport_serial,
                    info.department,
                    None,
                    None,
                ])

        # Instead of saving, write to BytesIO
        stream = BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream
