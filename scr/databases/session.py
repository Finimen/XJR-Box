import os
from scr.core.config import Settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

DATABASE_URL = Settings.DATABASE_URL

engine = create_async_engine(
    url = DATABASE_URL,
    echo = False,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)