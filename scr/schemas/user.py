from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

class UserLogin(BaseModel):
    username : str
    password : str

class UserRegister(BaseModel):
    username : str = Field(..., min_length=3, max_length=25)
    password : str
    email : EmailStr = Field(..., min_length=5)

class UserResponse(BaseModel):
    id: int
    username: str = Field(..., min_length=3, max_length=25)
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True