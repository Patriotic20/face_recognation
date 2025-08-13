from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException , status
from core.models.user import User
from src.core.utils.basic_service import BasicCrud


async def get_user_by_id(session: AsyncSession , user_id: int):
    user_data = await BasicCrud(db=session).get_by_id(model=User , item_id=user_id)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found by this id {user_id}"
        )


async def get_user_by_username(session: AsyncSession , username: str):
    user_data = await BasicCrud(db=session).get_by_field(model=User , field_name="username", field_value=username)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found by this id {username}"
        )
