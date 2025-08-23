import logging
from typing import Generic, TypeVar, Type, Any, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update, or_
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel

from core.models import Base

log = logging.getLogger(__name__)


ModelType = TypeVar("ModelType", bound=Base)
SchemaType = TypeVar("SchemaType", bound=BaseModel)


class BasicService(Generic[ModelType, SchemaType]):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, model: Type[ModelType], obj_items: SchemaType):
        try:
            log.debug(f"Creating {model.__name__} with data: {obj_items}")
            db_obj = model(**obj_items.model_dump())
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
            log.info(f"{model.__name__} created with ID: {getattr(db_obj, 'id', None)}")
            return db_obj
        except SQLAlchemyError as e:
            log.exception(f"Failed to create {model.__name__}")
            await self.db.rollback()
            raise e

    async def get_by_id(self, model: Type[ModelType], item_id: int):
        try:
            log.debug(f"Fetching {model.__name__} by ID: {item_id}")
            stmt = select(model).where(model.id == item_id)
            result = await self.db.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError as e:
            log.exception(f"Failed to fetch {model.__name__} by ID")
            await self.db.rollback()
            raise e

    async def get_all(
        self,
        model: Type[ModelType],
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Sequence] = None,
    ):
        try:
            log.debug(
                f"Fetching all {model.__name__} with limit={limit}, offset={offset}, filters={filters}"
            )
            stmt = select(model).offset(offset).limit(limit)
            if filters:
                stmt = stmt.where(and_(*filters))
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            log.exception(f"Failed to fetch all {model.__name__}")
            await self.db.rollback()
            raise e

    async def get_by_field(
        self, model: Type[ModelType], field_name: str, field_value: Any
    ):
        try:
            log.debug(f"Fetching {model.__name__} where {field_name}={field_value}")
            if not hasattr(model, field_name):
                raise AttributeError(
                    f"Field '{field_name}' does not exist on {model.__name__}"
                )
            stmt = select(model).where(getattr(model, field_name) == field_value)
            result = await self.db.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError as e:
            log.exception(f"Failed to fetch {model.__name__} by field {field_name}")
            await self.db.rollback()
            raise e

    async def update(
        self, 
        model: Type[ModelType], 
        obj_items: SchemaType,  
        item_id: int | None = None, 
        user_id: str | None = None
    ):
        try:
            log.debug(f"Updating {model.__name__} ID={item_id}, UserID={user_id} with data: {obj_items}")

            # Fetch object either by ID or user_id
            db_obj = None
            if item_id:
                db_obj = await self.get_by_id(model, item_id)
            if user_id:
                db_obj = await self.get_by_field(model=model, field_name="user_id", field_value=user_id)

            if not db_obj:
                log.warning(f"{model.__name__} with ID={item_id} or UserID={user_id} not found for update")
                return None

            # Extract only valid values
            valid_data = {
                key: value
                for key, value in obj_items.model_dump(exclude_unset=True).items()
                if value not in (None, "", "string")
            }

            # Apply updates
            for key, value in valid_data.items():
                setattr(db_obj, key, value)

            await self.db.commit()
            log.info(f"{model.__name__} updated successfully (ID={item_id}, UserID={user_id})")
            return db_obj

        except SQLAlchemyError:
            log.exception(f"Failed to update {model.__name__} (ID={item_id}, UserID={user_id})")
            await self.db.rollback()
            raise

    async def update_by_field(
        self,
        model: Type,
        field_name: str,
        field_value: Any,
        item_id: int | None = None,
        user_id: str | None = None,
    ):
        try:
            # Logging input
            log.debug(
                f"Updating field '{field_name}' of {model.__name__} "
                f"where id={item_id} or user_id={user_id} to value: {field_value}"
            )

            # Build WHERE conditions
            conditions = []
            if item_id is not None:
                conditions.append(model.id == item_id)
            if user_id is not None:
                conditions.append(model.user_id == user_id)

            if not conditions:
                raise ValueError("At least one of item_id or user_id must be provided.")

            stmt = (
                update(model)
                .where(or_(*conditions))
                .values({field_name: field_value})
                .execution_options(synchronize_session="fetch")
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            if result.rowcount == 0:
                log.warning(
                    f"No records updated in {model.__name__} where "
                    f"id={item_id} or user_id={user_id}"
                )
            else:
                log.info(
                    f"Updated {result.rowcount} record(s) in {model.__name__} "
                    f"for field '{field_name}'"
                )
            return result.rowcount

        except SQLAlchemyError as e:
            log.exception(
                f"Failed to update {model.__name__} field '{field_name}' "
                f"where id={item_id} or user_id={user_id}"
            )
            await self.session.rollback()
            raise e

    async def delete(self, model: Type[ModelType], item_id: int):
        try:
            log.debug(f"Deleting {model.__name__} with ID: {item_id}")
            db_obj = await self.get_by_id(model, item_id)
            if not db_obj:
                log.warning(
                    f"{model.__name__} with ID {item_id} not found for deletion"
                )
                return None
            await self.db.delete(db_obj)
            await self.db.commit()
            log.info(f"{model.__name__} with ID {item_id} deleted")
            return db_obj
        except SQLAlchemyError as e:
            log.exception(f"Failed to delete {model.__name__} with ID {item_id}")
            await self.db.rollback()
            raise e
