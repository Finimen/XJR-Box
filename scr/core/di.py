from mmap import ACCESS_COPY
from typing import AsyncGenerator

from fastapi import Depends
from scr.core.config import Settings
from scr.repositories.user_repository import UserRepository
from scr.services.auth import AuthService
from scr.services.email import EmailService
from sqlalchemy.ext.asyncio import AsyncSession
from scr.databases.session import async_session

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

async def get_config() -> Settings:
    return Settings()

async def get_email_service(
        config : Settings = Depends(get_config)
) -> EmailService:
    return EmailService()

async def get_auth_service(
        user_repository: UserRepository = Depends(get_user_repository),
        config : Settings = Depends(get_config),
        email_service: EmailService = Depends(get_email_service)
          ) -> AuthService:
    return AuthService(user_repository, email_service, config)
