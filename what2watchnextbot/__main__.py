import os

import aiogram

import what2watchnextbot.bot

bot = aiogram.Bot(os.environ["BOT_TOKEN"])
what2watchnextbot.bot.dispatcher.run_polling(bot)
