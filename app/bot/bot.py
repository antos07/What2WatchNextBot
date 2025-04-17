import aiogram
import aiogram.client.default
import pydantic
import pydantic_settings


class Config(pydantic_settings.BaseSettings, env_prefix="BOT_"):
    """Bot configuration.

    :ivar token: Bot token. Stored as ``pydantic.SecretStr``.
    :ivar parse_mode: Bot parse mode. Defaults to ``ParseMode.HTML``.
    """

    token: pydantic.SecretStr
    parse_mode: aiogram.enums.ParseMode = aiogram.enums.ParseMode.HTML


def create_bot(config: Config) -> aiogram.Bot:
    """Create a new bot instance from the given configuration.

    :param config: Bot configuration.
    :return: A new bot instance.
    """

    return aiogram.Bot(
        token=config.token.get_secret_value(),
        default=aiogram.client.default.DefaultBotProperties(
            parse_mode=config.parse_mode,
        ),
    )
