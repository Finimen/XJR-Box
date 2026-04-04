from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from scr.core.di import get_auth_service
from scr.models.user_model import UserModel
from scr.services.auth import AuthService


security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserModel:
    """
    Получить текущего пользователя из JWT токена.
    Используется как зависимость в protected endpoints.
    """
    # 1. Проверяем, есть ли токен
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # 2. Валидируем токен и получаем пользователя
    success, user, error = await auth_service.get_current_user(token)
    
    if not success or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error or "Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Возвращаем пользователя
    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[UserModel]:
    """
    Получить текущего пользователя, если токен есть и он валидный.
    Не кидает ошибку, если токена нет.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    success, user, _ = await auth_service.get_current_user(token)
    
    return user if success else None
