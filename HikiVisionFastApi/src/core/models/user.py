from sqlalchemy.orm import Mapped, mapped_column , relationship 
from .base import Base
from sqlalchemy import String , ForeignKey 


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user_logs import UserLog
    from .role import Role
    from .user_info import UserInfo



class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)  
    username: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String , nullable=True)
    image_path: Mapped[str] = mapped_column(String , nullable=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id") , nullable=True)
    
    
    user_logs: Mapped[list["UserLog"]] = relationship("UserLog" , back_populates="user")
    role: Mapped["Role"] = relationship("Role" , back_populates="user")
    user_info: Mapped["UserInfo"] = relationship("UserInfo" , back_populates="user")
