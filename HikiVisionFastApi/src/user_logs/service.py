from datetime import datetime , timezone , timedelta , date
from sqlalchemy import select , desc , and_ 
from sqlalchemy.orm import joinedload , selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from openpyxl import Workbook
from io import BytesIO

from core.utils.basic_service import BasicService
from core.models import UserLog , UserInfo , User
from .schemas import UserLogEnterCreate 



    
UTC_PLUS_5 = timezone(timedelta(hours=5))

class UserLogService:
    def __init__(self , session:AsyncSession):
        self.session = session
        self.service = BasicService(db=self.session)
    
    async def create_user_logs(self, user_log_create: UserLogEnterCreate):
        stmt = (
            select(UserLog)
            .where(
                UserLog.user_id == user_log_create.user_id,
                UserLog.exit_time.is_(None)  
            )
            .order_by(desc(UserLog.enter_time))  
            .limit(1)
        )

        result = await self.session.execute(stmt)
        user_log_data = result.scalars().first()

        
        if not user_log_data:
            return await self.service.create(model=UserLog, obj_items=user_log_create)

        
        current_date = datetime.now().date()
        date_from_ip = user_log_data.enter_time.date()

        if date_from_ip < current_date:

            return await self.service.create(model=UserLog, obj_items=user_log_create)

        
        return {"message": "You haven't exited yet, so you can't enter again."}


    
    async def get_user_logs_by_id(self,  user_log_id: int):
        return await self.service.get_by_id(model=UserLog , item_id=user_log_id)
    
    async def get_user_logs_by_user_id(self , user_id: int):
        return await self.service.get_by_field(model=UserLog , field_name="user_id" , field_value=user_id)
    
    async def get_all_user_logs(
        self,
        limit: int = 10,
        offset: int = 0,
        user_id: int | None = None,
        enter_date: date | None = None,
        exit_date: date | None = None,
    ):
        filters = []

        if user_id:
            filters.append(UserLog.user_id == user_id)

        if enter_date:
            start = datetime.combine(enter_date, datetime.min.time())
            end = start + timedelta(days=1)
            filters.append(and_(UserLog.enter_time >= start, UserLog.enter_time < end))

        if exit_date:
            start = datetime.combine(exit_date, datetime.min.time())
            end = start + timedelta(days=1)
            filters.append(and_(UserLog.exit_time >= start, UserLog.exit_time < end))

        stmt = (
            select(UserLog)
            .options(joinedload(UserLog.user))
            .limit(limit)
            .offset(offset)
        )

        if filters:
            stmt = stmt.where(and_(*filters))

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

    
    async def make_exel_file(
        self, 
        filter_data: date | None = None
    ) -> BytesIO:
        filters = []
        if filter_data:
            # use range filtering for performance
            start = datetime.combine(filter_data, datetime.min.time())
            end = start + timedelta(days=1)
            filters.append(and_(
                UserLog.enter_time >= start,
                UserLog.enter_time < end
            ))

        stmt = (
            select(User)
            .join(User.user_logs)  # ensure filtering applies
            .options(
                selectinload(User.user_info),
                selectinload(User.user_logs),
            )
            .where(*filters)
        )

        result = await self.session.execute(stmt)
        users = result.scalars().unique().all()

        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Users"

        # Header row
        header = [
            "First_name",
            "Last_name",
            "Third_name",
            "Passport_serial",
            "Department",
            "Enter_date",
            "Enter_time",
            "Exit_date",
            "Exit_time",
        ]
        ws.append(header)

        # Fill data
        for user in users:
            info = user.user_info
            if not info:
                continue  # skip if user_info is missing

            if user.user_logs:
                for log in user.user_logs:
                    ent = log.enter_time.astimezone(UTC_PLUS_5) if log.enter_time else None
                    ext = log.exit_time.astimezone(UTC_PLUS_5) if log.exit_time else None

                    ws.append([
                        info.first_name,
                        info.last_name,
                        info.third_name,
                        info.passport_serial,
                        info.department,
                        ent.strftime("%Y-%m-%d") if ent else None,
                        ent.strftime("%H:%M:%S") if ent else None,
                        ext.strftime("%Y-%m-%d") if ext else None,
                        ext.strftime("%H:%M:%S") if ext else None,
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
                    None,
                    None,
                ])

        # Write workbook to BytesIO
        stream = BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream

