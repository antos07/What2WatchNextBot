import os

import aiogram

from what2watchnextbot import logging
from what2watchnextbot.dispatcher import create_dispatcher

logging.configure(level="DEBUG")

dispatcher = create_dispatcher()
bot = aiogram.Bot(os.environ["BOT_TOKEN"])
dispatcher.run_polling(bot)
