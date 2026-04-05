from logging import getLogger
from typing import AsyncGenerator, Optional
from scr.services.scheduler import ScriptScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from scr.databases.session import async_session
from scr.core.config import settings
from scr.repositories.user_repository import UserRepository
from scr.repositories.scripts_repository import ScriptRepository
from scr.services.auth import AuthService
from scr.services.email import EmailService
from scr.services.redis import RedisService
from scr.services.script import ScriptService
from fastapi import Depends, Request

logger = getLogger(__name__)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session = async_session()
    try:
        yield session
    finally:
        await session.close()

async def get_redis_service(request: Request) -> RedisService:
    if not hasattr(request.app.state, 'redis_service'):
        raise RuntimeError("Redis service not initialized")
    return request.app.state.redis_service

async def get_email_service() -> EmailService:
    return EmailService()

def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_script_repository(db: AsyncSession = Depends(get_db)) -> ScriptRepository:
    return ScriptRepository(db)

async def get_auth_service(
    request: Request,
    user_repo: UserRepository = Depends(get_user_repository),
    email_service: EmailService = Depends(get_email_service),
    redis_service: RedisService = Depends(get_redis_service),
) -> AuthService:
    if not await redis_service.health_check():
        logger.critical("Redis is not available! Auth service cannot function properly.")
        raise RuntimeError("Authentication service unavailable due to Redis connection failure")

    return AuthService(user_repo, email_service, redis_service, settings)

async def get_script_service(
    script_repo: ScriptRepository = Depends(get_script_repository),
) -> ScriptService:
    return ScriptService(script_repo)

async def get_scheduler(request: Request) -> ScriptScheduler:
    if not hasattr(request.app.state, 'scheduler'):
        raise RuntimeError("Scheduler not initialized")
    return request.app.state.scheduler
