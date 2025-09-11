from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
from datetime import date , datetime 
from io import BytesIO

from core.utils.db_helper import db_helper
from .service import UserLogService 
from .schemas import UserLogsResponse

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
    limit: int = 20,
    offset: int = 0,
    user_id: str | None = None,
    enter_time: date | None = None,
    exit_time: date | None = None,
    
    service: UserLogService = Depends(get_user_log_service),
    _: User = Depends(role_checker("admin"))  
    ):
    return await service.get_all_user_logs(
        limit=limit, 
        offset=offset, 
        user_id=user_id, 
        enter_date=enter_time, 
        exit_date=exit_time
        )

@router.post("/create/exel")
async def create_exel(
    filter_date: datetime | None = Query(None, description="Filter by datetime"),
    service: UserLogService = Depends(get_user_log_service),
    _: User = Depends(role_checker("admin"))  
):
    filter_date_only = filter_date.date() if filter_date else None
    excel_stream: BytesIO = await service.make_exel_file(filter_data=filter_date_only)
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="users.xlsx"'}
    )


