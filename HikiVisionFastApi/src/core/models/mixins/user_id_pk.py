from sqlalchemy.orm import Mapped, mapped_column, declared_attr, relationship
from sqlalchemy import ForeignKey
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import User


class UserFkId:

    _user_back_populates: str | None = None

    @declared_attr
    def user_id(cls) -> Mapped[str]:
        return mapped_column(ForeignKey("users.username"))

    @declared_attr
    def user(cls) -> Mapped["User"]:
        return relationship("User", back_populates=cls._user_back_populates)
