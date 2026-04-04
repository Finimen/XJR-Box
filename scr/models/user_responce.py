from pydantic import BaseModel, EmailStr, Field

class UserResponce(BaseModel):
    name: str = Field(..., min_length=3, max_length=25)
    email: EmailStr

    class Config:
        from_attributes = True