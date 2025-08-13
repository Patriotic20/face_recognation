from .base import Base
from .mixins.int_id_pk import IntIdPkMixin
from sqlalchemy.orm import Mapped , relationship , mapped_column
from sqlalchemy import String
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user_logs import UserLog


class User(Base , IntIdPkMixin):
    
    username: Mapped[str] = mapped_column(String , unique=True , nullable=False)
    
    
    user_logs: Mapped[list["UserLog"]] = relationship("UserLog" , back_populates="user")
    
    
