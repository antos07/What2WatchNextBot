import aiogram

from what2watchnextbot import database

router = aiogram.Router(name=__name__)


@router.shutdown()
async def shutdown_db():
    await database.engine.dispose()
