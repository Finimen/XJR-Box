from mmap import ACCESS_COPY
from typing import AsyncGenerator, Optional

from fastapi import Depends
from scr.core.config import Settings, settings
from scr.repositories.scripts_repository import ScriptRepository
from scr.repositories.user_repository import UserRepository
from scr.services.auth import AuthService
from scr.services.email import EmailService
from scr.services.redis import RedisService
from scr.services.script import ScriptService
from sqlalchemy.ext.asyncio import AsyncSession
from scr.databases.session import async_session

_redis_service: Optional[RedisService] = None

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

async def get_redis_service() -> RedisService:
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
        await _redis_service.connect()
    return _redis_service

async def close_redis_connection():
    global _redis_service
    if _redis_service:
        await _redis_service.disconnect()

async def get_auth_service(
    user_repository: UserRepository = Depends(get_user_repository),
    email_service: EmailService = Depends(get_email_service),
    redis_service: RedisService = Depends(get_redis_service),  
) -> AuthService:
    return AuthService(user_repository, email_service, redis_service, settings)

async def get_script_repository(
    db: AsyncSession = Depends(get_db)
) -> ScriptRepository:
    return ScriptRepository(db)

async def get_script_service(
    script_repo: ScriptRepository = Depends(get_script_repository)
) -> ScriptService:
    return ScriptService(script_repo)
