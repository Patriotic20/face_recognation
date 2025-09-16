from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, time
from sqlalchemy import select

from .schemas import UserLogEnterCreate
from core.models.user import User
from core.models.role import Role


async def is_admin(session: AsyncSession, user_id: str) -> bool:
    stmt = (
        select(User.id)
        .join(Role)
        .where(User.id == user_id, Role.name == "admin")
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def admin_enter(session: AsyncSession, admin_data: UserLogEnterCreate):
    if not await is_admin(session, admin_data.user_id):
        return None  

    normalized_time = enter_time_to_range(admin_data.enter_time)
    
    return UserLogEnterCreate(
        user_id=admin_data.user_id,
        enter_time=normalized_time
    )


def enter_time_to_range(dt: datetime) -> datetime:
    start = time(7, 50)
    end = time(8, 10)

    if dt.time() < start:
        return dt.replace(hour=start.hour, minute=start.minute, second=0, microsecond=0)
    if dt.time() > end:
        return dt.replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)
    return dt 


async def admin_exit(session: AsyncSession, user_id: str, admin_exit_time: datetime):
    if not await is_admin(session, user_id):
        return None  

    normalized_time = exit_time_to_range(admin_exit_time)
    
    return normalized_time


def exit_time_to_range(dt: datetime) -> datetime:
    end = time(16, 10)

    if dt.time() < end:
        return dt.replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)
    return dt
