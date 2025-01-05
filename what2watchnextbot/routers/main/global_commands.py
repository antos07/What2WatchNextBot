import aiogram.filters
import aiogram.fsm.scene as scene

from what2watchnextbot.routers.main.scenes.suggestionscene import SuggestionScene

router = aiogram.Router(name=__name__)


@router.message(aiogram.filters.CommandStart())
async def start(message: aiogram.types.Message, scenes: scene.ScenesManager):
    await scenes.enter(SuggestionScene)
