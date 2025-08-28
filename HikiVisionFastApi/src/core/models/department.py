from .base import Base
from .mixins.int_id_pk import IntIdPkMixin
from sqlalchemy.orm import Mapped 




class Department(Base , IntIdPkMixin):
    
    name: Mapped[str]
    
    

