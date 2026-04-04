from fastapi import APIRouter, Depends, HTTPException
import fastapi
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from scr.core.di import get_auth_service
from scr.models.token import Token
from scr.schemas.user import UserLogin, UserRegister, UserResponce
from scr.services.auth import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/register", response_model=UserResponce)
async def register(user_data: UserRegister, auth_service : AuthService = Depends(get_auth_service)):
    success, user, error = await auth_service.register(
        username = user_data.username, 
        email = user_data.email,
        password = user_data.password
        )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return user

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    success, token, error = await auth_service.login(
        username = user_data.username,
        password = user_data.password
    )

    if not success:
        raise HTTPException(status_code=401, detail=error)

    return token

@router.post("/logout", response_model=JSONResponse)
async def logout():
    return JSONResponse(
        status_code=200,
        content = {"messege" : "OK"}
    )