from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from .service.append_two_service import UserService
from .service.user_crud_service import UserCrudService
from .service.user_info_service import UserInfoService
from core.utils.db_helper import db_helper
from auth.utils import role_checker
from .schemas import UserInfoBase
from core.models import User

router = APIRouter(prefix="/users", tags=["Users"])



def get_user_service(
    session: AsyncSession = Depends(db_helper.session_getter),
    device_ip: Optional[List[str]] = Query(None),  
) -> UserService:
    return UserService(session=session, devices=device_ip)

def get_crud_service(
    session: AsyncSession = Depends(db_helper.session_getter)
)-> UserCrudService:
    return UserCrudService(session=session)


@router.post("/create")
async def create_user(
    username: str = Form(...),
    file: UploadFile = File(...),
    first_name: str | None = Form(None),
    last_name: str | None = Form(None),
    third_name: str | None = Form(None),
    passport_serial: str | None = Form(None),
    department: str | None = Form(None),
    service: UserService = Depends(get_user_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.create_and_add_user_with_file(
        username=username,
        file=file,
        first_name=first_name,
        last_name=last_name,
        third_name=third_name,
        passport_serial=passport_serial,
        department=department,
    )


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



@router.delete("/delete/db/{user_id}")
async def delete_user(
    user_id: str,
    service: UserCrudService = Depends(get_crud_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.delete_user(user_id=user_id)




def get_user_info_service(
    session: AsyncSession = Depends(db_helper.session_getter)
    ):
    return UserInfoService(session=session)

@router.get("/get/user_info/{user_info_id}" , tags=["User Info"])
async def get_user_info_by_id(
    user_info_id: int,
    service: UserInfoService = Depends(get_user_info_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.get_user_info_by_id(user_info_id=user_info_id)


@router.get("/get/user_info/{user_id}" , tags=["User Info"])
async def get_user_info_by_id(
    user_id: str,
    service: UserInfoService = Depends(get_user_info_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.get_user_info_by_user_id(user_id=user_id)


@router.get("/user_infos" , tags=["User Info"])
async def get_all(
    limit: int = 20,
    offset: int = 0,
    service: UserInfoService = Depends(get_user_info_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.get_all_user_info(limit=limit , offset=offset)

@router.put("/update" , tags=["User Info"])
async def update(
    user_info_data: UserInfoBase,
    user_id:str | None = None,
    user_info_id: int | None = None,
    service: UserInfoService = Depends(get_user_info_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.update_user_info(user_id=user_id , user_info_id=user_info_id  , user_info_data=user_info_data)


@router.delete("/user_infos/delete/{user_id}", tags=["User Info"])
async def delete_user_info(
    user_id: str,
    service: UserInfoService = Depends(get_user_info_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.delete_user_info_by_user_id(user_id=user_id)

@router.delete("/user_infos/delete/{user_info_id}" , tags=["User Info"])
async def delete_user_info(
    user_info_id: int,
    service: UserInfoService = Depends(get_user_info_service),
    _: User = Depends(role_checker("admin")),
):
    return await service.delete_user_info_by_id(user_info_id=user_info_id)
