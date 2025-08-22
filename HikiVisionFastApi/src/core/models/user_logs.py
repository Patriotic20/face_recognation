from .base import Base
from .mixins.int_id_pk import IntIdPkMixin
from sqlalchemy.orm import Mapped , mapped_column , relationship
from datetime import datetime 
from sqlalchemy import DateTime , ForeignKey 


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User



class UserLog(Base , IntIdPkMixin):
    
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    enter_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True ), nullable=True )
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    
    user: Mapped["User"] = relationship("User" , back_populates="user_logs")
    
    

