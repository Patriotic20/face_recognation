from .user_crud_service import UserCrudService
from fastapi import UploadFile
from .hiki_vision_service import HikiUserService
from .user_info_service import UserInfoService
from sqlalchemy.ext.asyncio import AsyncSession
from user.schemas import UserBase, UserCreate , UserInfoBase , UserInfoCreate
from fastapi import HTTPException, status
from user.utils.make_random_code import make_random_code
from core.config import settings
from user.utils.file import save_file
from user.utils.image import compress_image_for_hikvision
from auth.utils import get_user


class UserService:
    default_devices = [
        "192.168.88.101",
        "192.168.88.102",
        "192.168.88.105",
        "192.168.88.106",
    ]
    
    def __init__(self, session: AsyncSession, devices: list[str] | None = None):
        self.session = session
        self.service = UserCrudService(session=self.session)
        
        self.user_info_service = UserInfoService(session=self.session)

        active_devices = devices if devices else self.default_devices
        self.hikivision_clients = [
            HikiUserService(ip_address=ip, username=settings.camera.username, password=settings.camera.password)
            for ip in active_devices
        ]

    async def create_and_add_user_with_file(
        self, 
        username: str, 
        file: UploadFile,
        first_name: str | None = None , 
        last_name: str | None = None, 
        third_name: str | None = None, 
        passport_serial: str | None = None, 
        department: str | None = None, 
        ):
        
        exit_user = await get_user(session=self.session, username=username)
        if exit_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already used"
            )
 
        # Save → Compress
        saved_path = await save_file(file)
        compressed_path = compress_image_for_hikvision(saved_path)

        # Prepare user
        user_data = UserCreate(
            username=username, 
            image_path=compressed_path , 
            first_name=first_name , 
            last_name=last_name , 
            third_name=third_name , 
            passport_serial=passport_serial, 
            department=department
            )
        return await self.create_and_add_user(user_data)

    async def create_and_add_user(self, user_data: UserCreate):
        user_id = make_random_code()

        # Create user
        user = await self.service.create_user(
            user_data=UserBase(
                id=user_id,
                username=user_data.username,
                image_path=user_data.image_path,
            )
        )

        if not user or not getattr(user, "id", None):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user",
            )

        # Create user info
        await self.user_info_service.create_user_info(
            user_info_data=UserInfoCreate(
                user_id=user_id,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                third_name=user_data.third_name,
                department=user_data.department,
                passport_serial=user_data.passport_serial,
            )
        )

        # Register user on Hikvision devices
        successes, errors = [], []
        for client in self.hikivision_clients:
            if await client.register_with_face(
                user_id=str(user.id),
                user_name=user.username,
                image_path=user_data.image_path,
            ):
                successes.append(client.ip_address)
            else:
                errors.append(client.ip_address)

        # Rollback user creation if failed everywhere
        if not successes:
            await self.service.delete_user(user.id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register user on all Hikvision devices",
            )

        return {
            "user": user,
            "hikvision_status": {
                "success": successes,
                "failed": errors,
            },
        }

    async def get_user_by_id(self , user_id: str):
        return await self.service.get_user_by_id(user_id=user_id)
        
        
    async def get_all_user(self, limit: int = 0 , offset: int = 0):
        return await self.service.get_all_users(limit=limit , offset=offset)


    async def update_user_and_hiki(self, user_id: str, new_name: str):
        successes, errors = [], []

        # Try updating all Hikvision devices first
        for client in self.hikivision_clients:
            success = await client.modify_user(
                user_id=user_id,
                new_name=new_name,
            )
            if success:
                successes.append(client.ip_address)
            else:
                errors.append(client.ip_address)

        # Update DB only if at least one device succeeded
        if successes:
            update_data = await self.service.update_user(
                user_id=user_id, 
                user_name=new_name
            )
        else:
            update_data = None  # no update since all failed

        return {
            "update_data": update_data,
            "successes": successes,
            "errors": errors,
        }
        
        
    async def delete_user_in_hiki(self, user_id: str):
        successes, errors = [], []

        # Try deleting user on all Hikvision devices first
        for client in self.hikivision_clients:
            success = await client.delete_user(user_id=user_id)
            if success:
                successes.append(client.ip_address)
            else:
                errors.append(client.ip_address)

        # Delete from DB only if at least one device succeeded
        if successes:
            await self.service.delete_user(user_id=user_id)
            db_deleted = True
        else:
            db_deleted = False

        return {
            "db_deleted": db_deleted,
            "successes": successes,
            "errors": errors,
        }

