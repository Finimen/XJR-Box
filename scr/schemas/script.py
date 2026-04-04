from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class ScriptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    code: str = Field(..., min_length=1)  # Python код
    schedule: Optional[str] = None  # "*/5 * * * *"

class ScriptUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    schedule: Optional[str] = None
    is_active: Optional[bool] = None

class ScriptResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    schedule: Optional[str]
    is_active: bool
    created_at: datetime
    last_run_at: Optional[datetime]
    
    class Config:
        from_attributes = True
