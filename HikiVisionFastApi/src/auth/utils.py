from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select 
from sqlalchemy.orm import joinedload
from core.models.user import User
from passlib.context import CryptContext
from datetime import datetime , timedelta , timezone
from fastapi.security import OAuth2PasswordBearer
from core.config import settings
import jwt
from fastapi import Depends , HTTPException , status
from typing import Annotated
from core.utils.db_helper import db_helper


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")



def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str , hashed_password:str )-> bool:
    return pwd_context.verify(plain_password , hashed_password)
    

async def get_user(session: AsyncSession, username: str):
    stmt = (
        select(User)
        .where(User.username == username)
        .options(joinedload(User.role))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()




async def authenticate_user(session: AsyncSession , username: str , password: str):
    user: User = await get_user(session=session , username=username)
    if not user:
        return False
    if not verify_password(plain_password=password , hashed_password=user.password):
        return False
    return user


def create_token(data: dict, secret_key: str, expires_delta: timedelta, algorithm: str) -> str:
    """Generic function to create JWT token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def create_access_token(data: dict) -> str:
    return create_token(
        data,
        secret_key=settings.jwt.access_secret_key,
        expires_delta=timedelta(minutes=settings.jwt.access_token_minutes),
        algorithm=settings.jwt.algorithm,
    )


def create_refresh_token(data: dict) -> str:
    return create_token(
        data,
        secret_key=settings.jwt.refresh_secret_key,
        expires_delta=timedelta(days=settings.jwt.refresh_token_days),
        algorithm=settings.jwt.algorithm,
    )
    
    
async def get_current_user(
    token: Annotated[str , Depends(oauth2_scheme)],
    session: AsyncSession = Depends(db_helper.session_getter),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt.access_secret_key, algorithms=[settings.jwt.algorithm])
        username = payload.get("username")
        if username is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = await get_user(session=session ,username=username)
    if user is None:
        raise credentials_exception
    return user




def role_checker(*allowed_roles: str):
    async def wrapper(user = Depends(get_current_user)):
        if not user.role or user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return user
    return wrapper
