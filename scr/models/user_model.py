from datetime import datetime
from typing import cast

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()

class UserModel(Base):
    __tablename__="users"

    id = Column(Integer, primary_key = True)
    username = Column(String(25), nullable = False, unique = True)
    password_hash = Column(String(200), nullable = False)
    email = Column(String(200), nullable = False, unique = True)
    created_at = Column(DateTime, default = datetime.utcnow())

    scripts = relationship("Script", back_populates="user", cascade="all, delete-orphan")

    @property
    def get_id(self) -> int:
        return cast(int, self.id)
    
    @property
    def get_username(self) -> str:
        return cast(str, self.username)
    
    @property
    def get_email(self) -> str:
        return cast(str, self.email)