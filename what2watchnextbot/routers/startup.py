import aiogram
from loguru import logger

from what2watchnextbot import commands

router = aiogram.Router(name=__name__)


@router.startup()
async def set_commands(bot: aiogram.Bot) -> None:
    """This handler sets the bot commands on startup."""

    await bot.set_my_commands(commands=commands.COMMANDS)
    logger.info("Set the bot commands")
