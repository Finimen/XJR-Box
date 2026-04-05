import os
from scr.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool

DATABASE_URL = settings.DATABASE_URL

if "postgresql" in DATABASE_URL:
    engine = create_async_engine(
        url=DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=20,                    
        max_overflow=10,                 
        pool_timeout=30,                 
        pool_recycle=3600,               
        pool_pre_ping=True,              
    )
else: 
    engine = create_async_engine(
        url=DATABASE_URL,
        echo=settings.DEBUG,
        poolclass=NullPool,              
    )

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)