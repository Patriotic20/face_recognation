from .user_crud_service import UserCrudService
from fastapi import UploadFile
from .hiki_vision_service import HikiUserService
from sqlalchemy.ext.asyncio import AsyncSession
from user.schemas import UserBase, UserCreate
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

        active_devices = devices if devices else self.default_devices
        self.hikivision_clients = [
            HikiUserService(ip_address=ip, username=settings.camera.username, password=settings.camera.password)
            for ip in active_devices
        ]

    async def create_and_add_user_with_file(self, username: str, file: UploadFile):
        
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
        user_data = UserCreate(username=username, image_path=compressed_path)
        return await self.create_and_add_user(user_data)

    async def create_and_add_user(self, user_data: UserCreate):
        user_id = make_random_code()

        user_info = UserBase(
            id=user_id,
            username=user_data.username,
            image_path=user_data.image_path,
        )
        user = await self.service.create_user(user_data=user_info)

        if not getattr(user, "id", None):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User ID not set",
            )

        successes, errors = [], []
        for client in self.hikivision_clients:
            success = await client.register_with_face(
                user_id=str(user.id),
                user_name=user.username,
                image_path=user_data.image_path,
            )
            if success:
                successes.append(client.ip_address)
            else:
                errors.append(client.ip_address)

        if not successes:
            await self.service.delete_user(user.id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register user on all Hikvision devices",
            )

        return {"user": user, "hikvision_status": {"success": successes, "failed": errors}}
