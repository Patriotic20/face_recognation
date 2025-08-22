from sqlalchemy.orm import Mapped , relationship
from core.models.base import Base

from .mixins.int_id_pk import IntIdPkMixin

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User

class Role(Base , IntIdPkMixin):
    
    name: Mapped[str]
    user: Mapped["User"] = relationship("User" , back_populates="role")
