from fastapi import APIRouter, Depends, HTTPException
import fastapi
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from scr.core.di import get_auth_service
from scr.core.tools import get_current_user
from scr.models.token import Token
from scr.models.user_model import UserModel
from scr.schemas.user import UserLogin, UserRegister, UserResponse
from scr.services.auth import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, auth_service : AuthService = Depends(get_auth_service)):
    success, user, error = await auth_service.register(
        username = user_data.username, 
        email = user_data.email,
        password = user_data.password
        )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        created_at=user.created_at
    )

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, auth_service: AuthService = Depends(get_auth_service)):
    success, token, error = await auth_service.login(
        username = user_data.username,
        password = user_data.password
    )

    if not success:
        raise HTTPException(status_code=401, detail=error)

    return Token(access_token = token, token_type = "bearer")

@router.post("/logout")
async def logout():
    return JSONResponse(
        status_code=200,
        content = {"messege" : "OK"}
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user)  # 👈 Используем зависимость
):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at
    )