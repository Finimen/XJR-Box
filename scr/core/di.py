from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from scr.databases.session import async_session
from scr.core.config import settings
from scr.repositories.user_repository import UserRepository
from scr.repositories.scripts_repository import ScriptRepository
from scr.services.auth import AuthService
from scr.services.email import EmailService
from scr.services.redis import RedisService
from scr.services.script import ScriptService
from fastapi import Depends

_redis_service: Optional[RedisService] = None
_scheduler: Optional[object] = None

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session = async_session()
    try:
        yield session
    finally:
        await session.close()

async def get_redis_service() -> RedisService:
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
        await _redis_service.connect()
    return _redis_service

async def get_email_service() -> EmailService:
    return EmailService()

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Создает UserRepository с переданной сессией"""
    return UserRepository(db)

def get_script_repository(db: AsyncSession = Depends(get_db)) -> ScriptRepository:
    """Создает ScriptRepository с переданной сессией"""
    return ScriptRepository(db)

async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    email_service: EmailService = Depends(get_email_service),
    redis_service: RedisService = Depends(get_redis_service),
) -> AuthService:
    return AuthService(user_repo, email_service, redis_service, settings)

async def get_script_service(
    script_repo: ScriptRepository = Depends(get_script_repository),
) -> ScriptService:
    return ScriptService(script_repo)

async def get_scheduler():
    global _scheduler
    if _scheduler is None:
        from scr.services.scheduler import ScriptScheduler
        _scheduler = ScriptScheduler(async_session)
    return _scheduler

async def close_redis_connection():
    global _redis_service
    if _redis_service:
        await _redis_service.disconnect()