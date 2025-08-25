from fastapi import APIRouter
from auth.api import router as auth_router
from role.api import router as role_router
from user.api import router as user_router
from user_logs.api import router as user_logs_router

router = APIRouter()


router.include_router(auth_router)
router.include_router(user_router)
router.include_router(user_logs_router)
router.include_router(role_router)


