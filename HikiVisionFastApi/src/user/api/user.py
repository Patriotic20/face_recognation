from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from user.service.append_two_service import UserService
from user.service.user_crud_service import UserCrudService
from core.utils.db_helper import db_helper
from auth.utils import role_checker
from user.schemas import UserBase , UserMe
from core.models import User

router = APIRouter(prefix="/users")



def get_user_service(
    session: AsyncSession = Depends(db_helper.session_getter),
    device_ip: Optional[List[str]] = Query(None),  
) -> UserService:
    return UserService(session=session, devices=device_ip)

def get_crud_service(
    session: AsyncSession = Depends(db_helper.session_getter)
)-> UserCrudService:
    return UserCrudService(session=session)


@router.post("/create" , tags=["Users"])
async def create_user(
    username: str = Form(...),
    file: UploadFile = File(...),
    first_name: str | None = Form(None),
    last_name: str | None = Form(None),
    third_name: str | None = Form(None),
    passport_serial: str | None = Form(None),
    department: str | None = Form(None),
    service: UserService = Depends(get_user_service),
    _: User = Depends(role_checker("admin" , "manager")),
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


@router.get("/{user_id}" , tags=["Users"] , response_model=UserMe)
async def get_by_id(
    user_id: str,
    service: UserService = Depends(get_user_service),
    _: User = Depends(role_checker("admin", "manager")),
):
    user_data = await service.get_user_by_id(user_id=user_id)
    return UserMe(
        id=user_data.id,
        username=user_data.username,
        image_path=user_data.image_path,
        role=user_data.role.name if user_data.role else None,
        user_info=user_data.user_info
    )


@router.get("" , tags=["Users"] , response_model=list[UserBase])
async def get_users(
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
    administration: bool = Query(False),
    service: UserService = Depends(get_user_service),
    username: str | None = None,
    _: User = Depends(role_checker("admin" , "manager")),
):
    return await service.get_all_user(administration=administration ,limit=limit, offset=offset, username=username)
    


@router.put("/update/{user_id}" , tags=["Users"])
async def update_user(
    user_id: str,
    new_name: str = Form(...),
    service: UserService = Depends(get_user_service),
    _: User = Depends(role_checker("admin" , "manager")),
):
    return await service.update_user_and_hiki(user_id=user_id, new_name=new_name)


@router.delete("/delete/{user_id}" , tags=["Users"])
async def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    _: User = Depends(role_checker("admin" , "manager")),
):
    return await service.delete_user_in_hiki(user_id=user_id)



@router.delete("/delete/db/{user_id}", tags=["Users"] )
async def delete_user(
    user_id: str,
    service: UserCrudService = Depends(get_crud_service),
    _: User = Depends(role_checker("admin")),
):
    await service.delete_user(user_id=user_id)
    return {"message": "Delete sucefully"}

