from datetime import datetime

from scr.models.user_model import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key = True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable = False)
    name = Column(String(255), nullable = False)
    description = Column(String(500))

    code = Column(Text, nullable = False)

    schedule  = Column(String(255))
    is_active = Column(Boolean, default = True)

    created_at = Column(DateTime, default = datetime.utcnow())
    updated_at = Column(DateTime, default = datetime.utcnow(), onupdate = datetime.utcnow())
    last_run_at = Column(DateTime, nullable = True)

    user = relationship("UserModel", back_populates="scripts")