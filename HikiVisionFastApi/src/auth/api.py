from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.utils.db_helper import db_helper
from .schemas import UserRegister , UserCredentials
from .service import AuthService
from auth.utils import role_checker

router = APIRouter(
    tags=["Auth"],
    prefix="/auth"
)

def get_auth_service(session: AsyncSession = Depends(db_helper.session_getter)):
    return AuthService(session=session)


@router.post("/login")  
async def login(
    credentials: UserCredentials = Depends(UserCredentials.as_form),
    service: AuthService = Depends(get_auth_service)
):
    return await service.login(credentials=credentials)

@router.post("/register")
async def register(
    credentials: UserRegister,
    service: AuthService = Depends(get_auth_service),
    _ = Depends(role_checker("admin"))
    
):
    await service.register(credentials=credentials)
    return {"message": "User created successfully"}



@router.post("/refresh")  
async def refresh(
    refresh_token: str,
    service: AuthService = Depends(get_auth_service)
):
    return await service.refresh(refresh_token=refresh_token)

