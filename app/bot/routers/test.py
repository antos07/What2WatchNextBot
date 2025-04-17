import aiogram
import aiogram.filters

from app.logging import logger

router = aiogram.Router(name=__name__)


@router.message(aiogram.filters.Command("ping"))
async def ping(message: aiogram.types.Message) -> None:
    await message.answer("pong")
    logger.info("Ping-pong")
