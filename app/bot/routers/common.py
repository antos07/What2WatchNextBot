"""This module contains a router that handles updates from all users."""

import aiogram.filters

from app.bot import scenes

router = aiogram.Router(name=__name__)

# Display the settings scene on /start if the user hasn't finished the first setup yet.
router.message.register(
    scenes.SettingsScene.as_handler(),
    aiogram.filters.CommandStart(),
    lambda _, user: not user.finished_first_setup,
)
