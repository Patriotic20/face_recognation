from datetime import datetime , timezone , timedelta , date , time
from sqlalchemy import select , desc , and_  , exists , not_
from sqlalchemy.orm import joinedload , selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from openpyxl import Workbook
from io import BytesIO

from core.utils.basic_service import BasicService
from core.models import UserLog , User
from .schemas import UserLogEnterCreate 




    
UTC_PLUS_5 = timezone(timedelta(hours=5))

class UserLogService:
    def __init__(self , session:AsyncSession):
        self.session = session
        self.service = BasicService(db=self.session)
    
    async def create_user_logs(self, user_log_create: UserLogEnterCreate):
        stmt = (
            select(UserLog)
            .where(UserLog.user_id == user_log_create.user_id)
            .order_by(desc(UserLog.enter_time))
            .limit(1)
        )

        result = await self.session.execute(stmt)
        user_log_data = result.scalars().first()


        # Case 1: No logs → create new
        if not user_log_data:
            return await self.service.create(model=UserLog, obj_items=user_log_create)

        # Case 2: Last log already closed → create new
        if user_log_data.exit_time is not None:
            return await self.service.create(model=UserLog, obj_items=user_log_create)

        # Case 3: Last log open but from previous day → create new
        current_date = datetime.now().date()
        enter_date = user_log_data.enter_time.date()
        if enter_date < current_date:
            return await self.service.create(model=UserLog, obj_items=user_log_create)

        # Case 4: Last log open today → reject
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

            if not user_log_data:
                return {"message": "You haven't entered, so you cannot exit."}

            enter_date = user_log_data.enter_time.date()
            exit_date = exit_time.date()

            if enter_date > exit_date:
                return {"message": "Exit time must be on the same day or after the enter time."}

            # ✅ Allow same day or later day
            user_log_data.exit_time = exit_time
            await self.session.commit()
            return user_log_data

    
    async def make_exel_file(
        self, 
        filter_data: date | None = None,
        attended_come: bool = True
        ) -> BytesIO:

        stmt = (
            select(User)
            .options(
                selectinload(User.user_info),
                selectinload(User.user_logs),
            )
        )
        
        if filter_data:
            start = datetime.combine(filter_data, time.min, tzinfo=UTC_PLUS_5)
            end = datetime.combine(filter_data, time.max, tzinfo=UTC_PLUS_5)

            # Subquery: does user have logs that day?
            log_exists = (
                select(UserLog.id)
                .where(
                    UserLog.user_id == User.id,
                    UserLog.enter_time >= start,
                    UserLog.enter_time <= end,
                )
            )
            
            if attended_come:
                stmt = stmt.where(exists(log_exists))
            else:
                stmt = stmt.where(not_(exists(log_exists)))
                
                
        result = await self.session.execute(stmt)
        users = result.scalars().unique().all()
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Users"

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

        for user in users:
            info = user.user_info
            if not info:
                continue

            # Only logs in selected day if filter_data given
            logs = user.user_logs
            if filter_data:
                logs = [
                    l for l in logs
                    if l.enter_time and start <= l.enter_time <= end
                ]

            if logs:
                for log in logs:
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
                # User has no logs (or filtered out)
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

        stream = BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream
