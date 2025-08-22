from sqlalchemy.ext.asyncio import AsyncSession 
from fastapi import HTTPException , status
from .schemas import UserCredentials , TokenData , UserRegister , UserCreate
from .utils import authenticate_user , create_access_token , create_refresh_token , get_user , hash_password
from core.utils.basic_service import BasicService
import jwt
from core.models import User , Role
from sqlalchemy import select 
from core.config import settings
from user.utils.make_random_code import make_random_code


class AuthService:
    def __init__(self , session: AsyncSession):
        self.session = session
        self.service = BasicService(db=self.session)
    
    async def login(self, credentials: UserCredentials) -> dict:
        user_data = await authenticate_user(
            session=self.session,
            username=credentials.username,
            password=credentials.password
        )
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token_data = TokenData(username=user_data.username, role=user_data.role.name).model_dump()

        return {
            "access_token": create_access_token(data=token_data),
            "refresh_token": create_refresh_token(data=token_data),
            "token_type": "bearer",
        }
        
    
    async def register(self, credentials: UserRegister):

        stmt = select(User).where(User.username == credentials.username, User.password.is_(None))
        user_with_no_password = (await self.session.execute(stmt)).scalar_one_or_none()
        
        existing_user_stmt = select(User).where(User.username == credentials.username, User.password.is_not(None))
        existing_user = (await self.session.execute(existing_user_stmt)).scalar_one_or_none()

        if existing_user:
            raise HTTPException(status_code=400, detail="User with this username already exists")

        

        role_stmt = select(Role).where(Role.name == credentials.role_name)
        role_data = (await self.session.execute(role_stmt)).scalar_one_or_none()

        if not role_data:
            raise HTTPException(status_code=400, detail=f"Role '{credentials.role_name}' not found")

        # --- Hash password ---
        hashed_password = hash_password(credentials.password)

        # --- Upgrade existing placeholder user ---
        if user_with_no_password:
            user_with_no_password.password = hashed_password
            user_with_no_password.role_id = role_data.id
            await self.session.commit()
            await self.session.refresh(user_with_no_password)
            return user_with_no_password

        # --- Otherwise create new user ---
        random_id = make_random_code()
        user_data = UserCreate(
            id=random_id,
            username=credentials.username,
            password=hashed_password,
            role_id=role_data.id,
        )
        return await self.service.create(model=User, obj_items=user_data)

            
    async def refresh(self , refresh_token: str):
        try:
            payload = jwt.decode(
                refresh_token,
                settings.jwt.refresh_secret_key,
                algorithms=[settings.jwt.algorithm],
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        username: str = payload.get("username")
        role: str = payload.get("role")
        
        
        if username is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        user = await get_user(self.session, username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        token_data = TokenData(username=user.username, role=user.role.name).model_dump()

        return {
            "access_token": create_access_token(data=token_data),
            "token_type": "bearer",
        }
