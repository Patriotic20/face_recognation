from core.models.base import Base
from sqlalchemy.orm import Mapped 
from .mixins.int_id_pk import IntIdPkMixin

class Admin(Base , IntIdPkMixin):
    
    username: Mapped[str]
    password: Mapped[str]
    
    
