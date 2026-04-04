from pydantic import BaseModel, EmailStr, Field

class UserLogin(BaseModel):
    username : str
    password : str

class UserRegister(BaseModel):
    username : str = Field(..., min_length=3, max_length=25)
    password : str
    email : str = Field(..., min_length=5)

class UserResponce(BaseModel):
    name: str = Field(..., min_length=3, max_length=25)
    email: EmailStr

    class Config:
        from_attributes = True