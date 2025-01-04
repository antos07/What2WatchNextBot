import logging
import os

import aiogram

import what2watchnextbot.bot

logging.basicConfig(level=logging.INFO)

bot = aiogram.Bot(os.environ["BOT_TOKEN"])
what2watchnextbot.bot.dispatcher.run_polling(bot)
