from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from user.service.user_info_service import UserInfoService
from core.utils.db_helper import db_helper
from auth.utils import role_checker
from user.schemas import UserInfoBase 
from core.models import User

router = APIRouter(
    tags=["User Info"],
    prefix="/user_info"
    )

def get_user_info_service(
    session: AsyncSession = Depends(db_helper.session_getter)
    ):
    return UserInfoService(session=session)

@router.get("/get/{user_info_id}")
async def get_user_info_by_id(
    user_info_id: int,
    service: UserInfoService = Depends(get_user_info_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.get_user_info_by_id(user_info_id=user_info_id)


@router.get("")
async def get_all(
    limit: int = 20,
    offset: int = 0,
    service: UserInfoService = Depends(get_user_info_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.get_all_user_info(limit=limit , offset=offset)

@router.put("/update")
async def update(
    user_info_data: UserInfoBase,
    user_id:str | None = None,
    user_info_id: int | None = None,
    service: UserInfoService = Depends(get_user_info_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.update_user_info(user_id=user_id , user_info_id=user_info_id  , user_info_data=user_info_data)


@router.delete("/delete/{user_id}")
async def delete_user_info(
    user_id: str,
    service: UserInfoService = Depends(get_user_info_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.delete_user_info_by_user_id(user_id=user_id)

@router.delete("/delete/{user_info_id}")
async def delete_user_info(
    user_info_id: int,
    service: UserInfoService = Depends(get_user_info_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.delete_user_info_by_id(user_info_id=user_info_id)
