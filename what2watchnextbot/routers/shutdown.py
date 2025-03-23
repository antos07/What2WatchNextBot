import aiogram
from loguru import logger

router = aiogram.Router(name=__name__)


@router.shutdown()
async def shutdown_db(engine):
    logger.debug("Shutting the SA engine down")
    await engine.dispose()
    logger.info("Shut down SA engine")


@router.shutdown()
async def complete_logging():
    await logger.complete()
