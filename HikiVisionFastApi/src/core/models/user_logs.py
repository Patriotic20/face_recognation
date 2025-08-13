from .base import Base
from .mixins.int_id_pk import IntIdPkMixin
from sqlalchemy.orm import Mapped , mapped_column
from datetime import datetime 
from sqlalchemy import DateTime 


class UserLog(Base , IntIdPkMixin):
    
    user_id: Mapped[str] 
    enter_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True ), nullable=True )
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    

