"""This module contains a router that should handle special cases that don't
really fall under any other category.

Most fallback handlers are also defined here, so this router should be the last to be
included.
"""

from contextlib import suppress
from typing import Final

import aiogram
from loguru import logger

router: Final[aiogram.Router] = aiogram.Router(name=__name__)


@router.callback_query()
async def answer_unhandled_callback_query(
    callback_query: aiogram.types.CallbackQuery,
) -> None:
    """Answer the callback query that wasn't handled by any other handler.

    :param callback_query: An incoming callback query.
    """

    logger.warning(f"Unhandled {callback_query.data=}")

    with suppress(Exception):
        await callback_query.answer()
