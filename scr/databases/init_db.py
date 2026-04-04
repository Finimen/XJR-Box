from logging import getLogger

from scr.databases.session import engine
from scr.models.user_model import Base

logger = getLogger(__name__)

async def init_db():
    async with engine.begin() as conn:
        logger.info("dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("create all teables...")
        await conn.run_sync(Base.metadata.create_all)

    logger.info("database tables created")