from fastapi import APIRouter, Depends
from core.utils.db_helper import db_helper
from .service import UserLogService 
from .schemas import UserLogsResponse
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import User 
from auth.utils import role_checker

router = APIRouter(
    tags=["User Logs"],
    prefix="/user_logs"
)

def get_user_log_service(session: AsyncSession = Depends(db_helper.session_getter)):
    return UserLogService(session=session)

@router.get("" , response_model=list[UserLogsResponse])
async def get_all_user_logs(
    service: UserLogService = Depends(get_user_log_service),
    _: User = Depends(role_checker("admin"))  
    ):
    return await service.get_all_user_logs()
    

