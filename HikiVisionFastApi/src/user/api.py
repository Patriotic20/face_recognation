from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from .service.append_two_service import UserService
from core.utils.db_helper import db_helper
from auth.utils import role_checker
from core.models import User

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/")
async def create_user(
    session: AsyncSession = Depends(db_helper.session_getter),
    username: str = Form(...),
    file: UploadFile = File(...),
    device_ip: list[str] = Form(None),
    _: User = Depends(role_checker("admin"))   
):
    service = UserService(session=session, devices=device_ip)
    return await service.create_and_add_user_with_file(username=username, file=file)
