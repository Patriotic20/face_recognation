from .base import Base
from .mixins.int_id_pk import IntIdPkMixin
from sqlalchemy.orm import Mapped , mapped_column  , relationship
from sqlalchemy import ForeignKey
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


class UserInfo(Base , IntIdPkMixin):
    
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    
    first_name: Mapped[str | None] 
    last_name: Mapped[str | None]
    third_name: Mapped[str | None]
    passport_serial: Mapped[str | None]
    department: Mapped[str | None]
    
    
    user: Mapped["User"] = relationship("User" , back_populates="user_info")
    
    
    
