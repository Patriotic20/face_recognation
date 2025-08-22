from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from .service.append_two_service import UserService
from core.utils.db_helper import db_helper
from auth.utils import role_checker
from core.models import User

router = APIRouter(prefix="/users", tags=["Users"])



def get_user_service(
    session: AsyncSession = Depends(db_helper.session_getter),
    device_ip: Optional[List[str]] = Query(None),  
) -> UserService:
    return UserService(session=session, devices=device_ip)



@router.post("/create")
async def create_user(
    username: str = Form(...),
    file: UploadFile = File(...),
    service: UserService = Depends(get_user_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.create_and_add_user_with_file(username=username, file=file)


@router.get("/{user_id}")
async def get_by_id(
    user_id: str,
    service: UserService = Depends(get_user_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.get_user_by_id(user_id=user_id)


@router.get("")
async def get_users(
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
    service: UserService = Depends(get_user_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.get_all_user(limit=limit, offset=offset)


@router.put("/update/{user_id}")
async def update_user(
    user_id: str,
    new_name: str = Form(...),
    service: UserService = Depends(get_user_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.update_user_and_hiki(user_id=user_id, new_name=new_name)


@router.delete("/delete/{user_id}")
async def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.delete_user_in_hiki(user_id=user_id)


    


