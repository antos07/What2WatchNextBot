import datetime

import aiogram
from aiogram.fsm.storage.base import StorageKey

BOT_TOKEN = "12345:AAAAAAAAAAAAA"
RANDOM_DATETIME = datetime.datetime(2025, 1, 17, 17, 17, 17)


REDIS_URL = "redis://localhost:6379/0"
DB_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"

TG_USER = aiogram.types.User(id=1, is_bot=False, first_name="John")
TITLE_BASICS_DATASET_HEADER = (
    "tconst\ttitleType\tprimaryTitle\toriginalTitle\tisAdult\tstartYear\t"
    "endYear\truntimeMinutes\tgenres\n"
)
TITLE_RATINGS_DATASET_HEADER = "tconst\taverageRating\tnumVotes\n"

STORAGE_KEY = StorageKey(bot_id=0, chat_id=0, user_id=0)
