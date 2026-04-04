from datetime import datetime

from scr.models.user_model import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class Execution(Base):
    __tablename__ = "executions"
    
    id = Column(__name_pos=Integer, primary_key=True)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=False)
    
    status = Column(String(50))  # "running", "success", "failed", "timeout"
    output = Column(Text)
    error = Column(Text)
    duration_ms = Column(Integer)  # время выполнения
    
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    
    # Отношения
    script = relationship("Script", back_populates="executions")
