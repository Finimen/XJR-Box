from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class ExecutionResponse(BaseModel):
    id: int
    script_id: int
    status: str
    output: Optional[str]
    error: Optional[str]
    duration_ms: Optional[int]
    started_at: datetime
    finished_at: Optional[datetime]
