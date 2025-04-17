from aiogram.enums import ParseMode

from app.bot.bot import Config, create_bot
from app.testing.constants import BOT_TOKEN


class TestCreateBot:
    def test_configuring_token_works(self) -> None:
        config = Config(token=BOT_TOKEN)

        bot = create_bot(config)
        assert bot.token == BOT_TOKEN

    def test_default_parse_mode_is_html(self) -> None:
        config = Config(token=BOT_TOKEN)

        bot = create_bot(config)
        assert bot.default.parse_mode == ParseMode.HTML
