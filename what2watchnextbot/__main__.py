import logging
import os

import aiogram

from what2watchnextbot.dispatcher import create_dispatcher

logging.basicConfig(level=logging.DEBUG)

dispatcher = create_dispatcher()
bot = aiogram.Bot(os.environ["BOT_TOKEN"])
dispatcher.run_polling(bot)
