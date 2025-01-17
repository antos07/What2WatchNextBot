import aiogram.filters
import aiogram.fsm.scene as scene
import aiogram.utils.formatting as fmt
from loguru import logger

from what2watchnextbot.routers.main.scenes.suggestionscene import SuggestionScene

router = aiogram.Router(name=__name__)


@router.message(aiogram.filters.CommandStart())
async def start(message: aiogram.types.Message, scenes: scene.ScenesManager):
    logger.info("/start command")
    await scenes.enter(SuggestionScene)


@router.message(aiogram.filters.Command("help"))
async def help(message: aiogram.types.Message) -> None:
    """This function handles /help command."""

    text = fmt.as_list(
        fmt.as_section(
            fmt.Bold("Who am I?"),
            "I can help you find something to watch. "
            "Of course, I'm far from being a modern AI chatbot, and, to be honest, "
            "I'm not an AI at all. But still, give me a try 🥺",
        ),
        fmt.as_section(
            fmt.Bold("How do I work?"),
            "So, to help you I downloaded the entire ",
            fmt.TextLink("IMDB", url="https://www.imdb.com/"),
            " database and provided some filters that you can use "
            "(I hope you've already seen them). "
            "After you adjust them to your liking, "
            "I simply suggest you random titles. That's all!",
        ),
        fmt.as_section(
            fmt.Bold("How can you help me to improve?"),
            "If you notice a bug or think some functionality is missing, "
            "feel free to contact my developer, @antos07",
        ),
        sep="\n\n",
    )
    await message.answer(**text.as_kwargs(), disable_web_page_preview=True)
    logger.info("Answered to a /help command")
