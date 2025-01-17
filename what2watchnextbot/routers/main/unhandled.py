import aiogram
from aiogram.types import CallbackQuery
from loguru import logger

router = aiogram.Router(name=__name__)


@router.callback_query()
async def unhandled_callback_query(callback_query: CallbackQuery) -> None:
    logger.info(
        f"Unhandled callback query: {callback_query.id=}, {callback_query.data=}"
    )

    await callback_query.answer(
        text="❌ This menu is no longer available", show_alert=True, cache_time=60
    )
