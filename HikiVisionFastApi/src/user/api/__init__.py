from fastapi import APIRouter

from .user import router as user_router 
from .user_info import router as user_info_router


router = APIRouter()


router.include_router(user_router)
router.include_router(user_info_router)

