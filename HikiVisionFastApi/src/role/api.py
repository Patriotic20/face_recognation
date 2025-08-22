from fastapi import APIRouter , Depends
from .service import RoleService
from .schemas import RoleCreate , RoleUpdate
from core.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from core.utils.db_helper import db_helper
from auth.utils import role_checker

router = APIRouter(
    prefix="/roles",
    tags=["Role"]
)

def get_role_service(session: AsyncSession = Depends(db_helper.session_getter)):
    return RoleService(session=session)


@router.post("/create")
async def create(
    role_data: RoleCreate,
    service: RoleService = Depends(get_role_service),
    # _: User = Depends(role_checker("admin"))
):
    return await service.create_role(role_data=role_data)



@router.get("/{role_id}")
async def get_by_id(
    role_id: int,
    service: RoleService = Depends(get_role_service),
    _: User = Depends(role_checker("admin"))
):
    return await service.get_role_by_id(role_id=role_id)



@router.get("")
async def get_all(
    limit: int = 20,
    offset: int = 0,
    service: RoleService = Depends(get_role_service),
    _: User = Depends(role_checker("admin"))
):
    return await service.get_all_roles(limit=limit , offset=offset)



@router.put("/update/{role_id}")
async def update(
    role_id: int,
    role_data: RoleUpdate,
    service: RoleService = Depends(get_role_service),
    _: User = Depends(role_checker("admin"))
):
    return await service.update_role(role_id=role_id, role_data=role_data)


@router.delete("/delete/{role_id}")
async def delete(
    role_id: int,
    service: RoleService = Depends(get_role_service),
    _: User = Depends(role_checker("admin"))
):
    return await service.delete_role(role_id=role_id)
