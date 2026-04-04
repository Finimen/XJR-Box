from logging import getLogger

logger = getLogger(__name__)

class EmailService:

    async def send_verification(self):
        logger.info("this feature in devolopment")