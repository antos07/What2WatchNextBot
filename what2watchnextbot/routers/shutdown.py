import aiogram
from loguru import logger

from what2watchnextbot import database

router = aiogram.Router(name=__name__)


@router.shutdown()
async def shutdown_db():
    logger.debug("Shutting the SA engine down")
    await database.engine.dispose()
    logger.info("Shut down SA engine")
