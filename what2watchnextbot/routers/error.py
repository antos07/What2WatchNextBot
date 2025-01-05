import aiogram
from loguru import logger

router = aiogram.Router(name=__name__)


@router.error()
async def unhandled_exception_handler(event: aiogram.types.ErrorEvent) -> None:
    logger.opt(exception=event.exception).error(
        f"Unhandled exception: {event.exception}"
    )
