from core.utils.basic_service import BasicService
from sqlalchemy.ext.asyncio import AsyncSession
from .schemas import RoleCreate , RoleUpdate
from core.models.role import Role


class RoleService:
    
    def __init__(self , session: AsyncSession):
        self.session = session
        self.service = BasicService(db=self.session)

    async def create_role(self , role_data: RoleCreate):
        return await self.service.create(model=Role , obj_items=role_data)
    
    async def get_role_by_id(self , role_id: int):
        return await self.service.get_by_id(model=Role , item_id=role_id)
    
    async def get_all_roles(self, limit: int = 20 , offset: int = 0):
        return await self.service.get_all(model=Role, limit=limit , offset=offset)
    
    async def update_role(self, role_id: int, role_data: RoleUpdate):
        return await self.service.update(item_id=role_id , model=Role , obj_items=role_data)
        
    async def delete_role(self , role_id: int):
        return await self.service.delete(model=Role , item_id=role_id)
        
