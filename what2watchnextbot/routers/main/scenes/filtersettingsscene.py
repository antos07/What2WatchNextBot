"""This module provides the filter settings scene."""

import asyncio
from collections.abc import Awaitable, Callable

import aiogram.exceptions
import aiogram.filters.callback_data as cd
import aiogram.types
import aiogram.utils.formatting as fmt
import aiogram.utils.keyboard as kb
import sqlalchemy.ext.asyncio as async_sa
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, on
from loguru import logger

from what2watchnextbot import models
from what2watchnextbot.genrepreferences import GenrePreferences


class SelectGenreCD(cd.CallbackData, prefix="select_genre"):
    """A callback data for selecting or unselecting a genre in genre selection
    preferences.

    :ivar genre_id: The ID of the genre.
    :ivar selected: The genre's new state.
    """

    genre_id: int
    selected: bool


class SelectAllGenresCD(cd.CallbackData, prefix="select_all_genres"):
    """A callback data for selecting or unselecting all genres in genre selection
    preferences.

    :ivar selected: The toggle's new state.
    """

    selected: bool


class SetGenreCombinatorModeCD(cd.CallbackData, prefix="set_genre_combinator_mode"):
    """A callback data changing genre combinator mode.

    :ivar require_all: A new mode.
    """

    require_all: bool


class MenuItem:
    """A base class for managing a menu item of the :class:`FilterSettingsScene`.

    As stated in :class:`FilterSettingsScene` docs, a menu item is a single message
    that can be sent, updated or closed (not deleted but all controls will be removed).
    This class provides a simple interface to perform these tasks.

    To create a new menu item, create a subclass of this class. In this class, you
    should define two class variables: ``fsm_key`` and ``text``. The first one is
    a key by which the menu state is stored in the FSM context data. The second one
    is a static text of the menu item (dynamic items should be displayed as an inline
    keyboard).

    There is an additional class variable ``build_additional_final_text`` that defaults
    to ``None``. In case you want to add some additional text when the menu item
    is closed (e.g., display saved settings in text), you should define an async method
    with this name that takes no arguments and returns the additional text.

    For example:

    .. code-block::

        class ExampleMenuItem(MenuItem):
            fsm_key = 'example'
            text = fmt.Text('Hello')1

            async def build_additional_final_text(self):
                return fmt.Text('I was closed')

    To build a dynamic keyboard, you should override :meth:`build_keyboard` method.
    It will be used by :meth:`send` and :meth:`update` methods. It can return either
    a reply or an inline reply markup. However, reply markup support is currently
    limited, so you should also override :meth:`close` and :meth:`update` methods
    to get them work properly
    (they will raise :exc:`aiogram.exceptions.BadRequest` otherwise).

    :cvar fsm_key: It is a key by which the menu state is stored
        in the FSM context data. Should be overridden by subclasses.
    :cvar text: It is a static text of the menu item.
        Should be overridden by subclasses.
    :cvar build_additional_final_text: Optional. An async function that takes no
        arguments and returns the additional text that will be rendered under
        the main text when the menu item is closed.

    :ivar bot: A bot that manages the menu item.
    :ivar chat: A chat, where the menu item is displayed.
    :ivar state: The FSM context.
    :ivar genre_preferences: A genre preferences manager.

    :param bot: A bot that manages the menu item.
    :param chat: A chat, where the menu item is displayed.
    :param state: The FSM context.
    :param genre_preferences: A genre preferences manager.
    """

    fsm_key: str
    text: fmt.Text
    build_additional_final_text: Callable[[], Awaitable[fmt.Text]] | None = None

    def __init__(
        self,
        bot: aiogram.Bot,
        chat: aiogram.types.Chat,
        state: FSMContext,
        genre_preferences: GenrePreferences,
    ) -> None:
        self.bot = bot
        self.chat = chat
        self.state = state
        self.genre_preferences = genre_preferences

    async def send(self) -> None:
        """A method to send the menu item.

        It sends a text message containing the static text and a keyboard built using
        :meth:`build_keyboard` method. ``message_id`` of the sent message is saved to
        the FSM context data.
        """

        reply_markup = await self.build_keyboard()

        logger.debug(
            f"sending message: chat_id={self.chat.id}, "
            f"text={self.text!r}, "
            f"reply_markup={reply_markup!r}"
        )
        sent_message = await self.bot.send_message(
            chat_id=self.chat.id,
            **self.text.as_kwargs(),
            reply_markup=reply_markup,
        )

        await self._save_message_id(sent_message.message_id)

    async def update(self) -> None:
        """A method to update the menu item.

        It updates the keyboard of the previously sent menu item.

        Using this method, when there was no inline keyboard before, will result
        in :exc:`aiogram.exceptions.BadRequest` being raised.
        """

        message_id = await self._get_message_id()
        reply_markup = await self.build_keyboard()

        logger.debug(
            f"editing message: chat_id={self.chat.id}, "
            f"message_id={message_id}, "
            f"text={self.text!r}, "
            f"reply_markup={reply_markup!r}"
        )
        await self.bot.edit_message_reply_markup(
            chat_id=self.chat.id,
            message_id=message_id,
            reply_markup=await self.build_keyboard(),
        )

    async def close(self) -> None:
        """A method to close the menu item.

        It removes the keyboard of the previously sent menu item and updates the text
        with additional final text,
        if :attr:`build_additional_final_text` is not ``None``.

        Using this method, when there was no inline keyboard before, will result
        in :exc:`aiogram.exceptions.BadRequest` being raised.
        """

        text = self.text
        if self.build_additional_final_text:
            text = fmt.Text(text, "\n\n", await self.build_additional_final_text())

        message_id = await self._get_message_id()

        logger.debug(
            f"editing message: chat_id={self.chat.id}, "
            f"message_id={message_id}, "
            f"text={text!r}"
        )
        await self.bot.edit_message_text(
            chat_id=self.chat.id, message_id=message_id, **text.as_kwargs()
        )

    async def build_keyboard(
        self,
    ) -> kb.InlineKeyboardMarkup | kb.ReplyKeyboardMarkup | None:
        """A method to build a keyboard for this menu item."""

        pass

    async def _save_message_id(self, message_id: int) -> None:
        """Save the message_id to the FSM context data."""

        await self.state.update_data({self.fsm_key: message_id})

    async def _get_message_id(self) -> int:
        """Get the message_id from the FSM context data."""

        value = await self.state.get_value(self.fsm_key)
        if value is None:
            raise KeyError(
                f"The FSM context data does not contain a key {self.fsm_key!r}"
            )
        return value


CLOSE_SETTINGS_BTN = "Close Settings"


class TitleMenuItem(MenuItem):
    """A menu item that contains the settings title.

    :cvar fsm_key: It is a key by which the menu state is stored
        in the FSM context data.
    :cvar text: It is a static text of the menu item.

    :ivar bot: A bot that manages the menu item.
    :ivar chat: A chat, where the menu item is displayed.
    :ivar state: The FSM context.
    :ivar genre_preferences: A genre preferences manager.

    :param bot: A bot that manages the menu item.
    :param chat: A chat, where the menu item is displayed.
    :param state: The FSM context.
    :param genre_preferences: A genre preferences manager.
    """

    fsm_key = "title"
    text = fmt.Bold("Settings")

    async def build_keyboard(self) -> kb.ReplyKeyboardMarkup:
        return (
            kb.ReplyKeyboardBuilder()
            .button(text=CLOSE_SETTINGS_BTN)
            .as_markup(resize_keyboard=True)
        )

    async def close(self) -> None:
        # do nothing
        pass

    async def update(self) -> None:
        # do nothing
        pass


class SelectTitleTypeCD(cd.CallbackData, prefix="select_title_type"):
    """A callback data for selecting or unselecting a title type in title type
    selection preferences.

    :ivar title_type: The title type.
    :ivar selected: The genre's new state.
    """

    title_type: models.TitleTypes
    selected: bool


class TitleTypeSelectorMenuItem(MenuItem):
    """A menu item that contains the title type selection preferences.

    :cvar fsm_key: It is a key by which the menu state is stored
        in the FSM context data.
    :cvar text: It is a static text of the menu item.

    :ivar bot: A bot that manages the menu item.
    :ivar chat: A chat, where the menu item is displayed.
    :ivar state: The FSM context.
    :ivar genre_preferences: A genre preferences manager.

    :param bot: A bot that manages the menu item.
    :param chat: A chat, where the menu item is displayed.
    :param state: The FSM context.
    :param genre_preferences: A genre preferences manager.
    """

    fsm_key = "title_type_selector"
    text = fmt.as_section(
        fmt.Underline("Types"),
        "Select title types that you are interested in.",
    )

    title_type_to_name = {
        models.TitleTypes.MOVIE: "Movie",
        models.TitleTypes.SERIES: "Series",
        models.TitleTypes.MINI_SERIES: "Mini Series",
    }

    async def build_additional_final_text(self) -> fmt.Text:
        selected_title_types = await self.genre_preferences.list_selected_title_types()
        selected_title_types = [
            self.title_type_to_name[title_type] for title_type in selected_title_types
        ]
        if selected_title_types:
            return fmt.as_marked_list(*selected_title_types, marker="✅ ")
        return fmt.Text()

    async def build_keyboard(self) -> kb.InlineKeyboardMarkup:
        selected_title_types = await self.genre_preferences.list_selected_title_types()

        builder = kb.InlineKeyboardBuilder()
        for title_type, name in self.title_type_to_name.items():
            selected = title_type in selected_title_types
            prefix = "✅ " if selected else ""
            builder.button(
                text=prefix + name,
                callback_data=SelectTitleTypeCD(
                    title_type=title_type, selected=not selected
                ),
            )

        return builder.as_markup()


class GenreSelectorMenuItem(MenuItem):
    """A menu item that provides genre selection preferences.

    :cvar fsm_key: It is a key by which the menu state is stored
        in the FSM context data.
    :cvar text: It is a static text of the menu item.

    :ivar bot: A bot that manages the menu item.
    :ivar chat: A chat, where the menu item is displayed.
    :ivar state: The FSM context.
    :ivar genre_preferences: A genre preferences manager.

    :param bot: A bot that manages the menu item.
    :param chat: A chat, where the menu item is displayed.
    :param state: The FSM context.
    :param genre_preferences: A genre preferences manager.
    """

    fsm_key = "genre_selector"
    text = fmt.as_section(
        fmt.Underline("Genres"),
        "Select genre(s) that you interested in.",
    )

    async def build_additional_final_text(self) -> fmt.Text:
        genres = [
            genre.name for genre in await self.genre_preferences.list_selected_genres()
        ]
        return fmt.as_marked_list(*genres, marker="✅ ") if genres else fmt.Text()

    async def build_keyboard(self) -> kb.InlineKeyboardMarkup:
        all_genres = await self.genre_preferences.get_all_genres()

        builder = kb.InlineKeyboardBuilder()
        for genre in all_genres:
            selected = await self.genre_preferences.is_genre_selected(genre.id)
            emoji = "✅" if selected else "☑"
            builder.button(
                text=f"{emoji} {genre.name}",
                callback_data=SelectGenreCD(genre_id=genre.id, selected=not selected),
            )
        builder.adjust(2, repeat=True)

        if await self.genre_preferences.are_all_genres_selected():
            button = aiogram.types.InlineKeyboardButton(
                text="Unselect All",
                callback_data=SelectAllGenresCD(selected=False).pack(),
            )
        else:
            button = aiogram.types.InlineKeyboardButton(
                text="Select All",
                callback_data=SelectAllGenresCD(selected=True).pack(),
            )
        builder.row(button)

        return builder.as_markup()


class GenreCombinatorMenuItem(MenuItem):
    """A menu item that provides genre combinator preferences.

    :cvar fsm_key: It is a key by which the menu state is stored
        in the FSM context data.
    :cvar text: It is a static text of the menu item.

    :ivar bot: A bot that manages the menu item.
    :ivar chat: A chat, where the menu item is displayed.
    :ivar state: The FSM context.
    :ivar genre_preferences: A genre preferences manager.

    :param bot: A bot that manages the menu item.
    :param chat: A chat, where the menu item is displayed.
    :param state: The FSM context.
    :param genre_preferences: A genre preferences manager.
    """

    fsm_key = "genre_combinator"
    text = fmt.as_section(
        fmt.Underline("How to combine genres?"),
        "Require titles to have ",
        fmt.Italic("all"),
        " or ",
        fmt.Italic("at least 1"),
        " of the selected genres.",
    )

    async def build_additional_final_text(self) -> fmt.Text:
        all_selected_genres_are_required = (
            await self.genre_preferences.check_all_selected_genres_are_required()
        )
        return fmt.Text(
            "✅ ",
            "All" if all_selected_genres_are_required else "At Least 1",
        )

    async def build_keyboard(self) -> kb.InlineKeyboardMarkup:
        builder = kb.InlineKeyboardBuilder()
        if await self.genre_preferences.check_all_selected_genres_are_required():
            builder.button(
                text="All", callback_data=SetGenreCombinatorModeCD(require_all=False)
            )
        else:
            builder.button(
                text="At Least 1",
                callback_data=SetGenreCombinatorModeCD(require_all=True),
            )
        return builder.as_markup()


class MinimumRatingCD(cd.CallbackData, prefix="minimum_rating"):
    """Callback data for selecting minimum title rating.

    :ivar rating: The minimum rating.
    """

    rating: int


class MinimumRatingMenuItem(MenuItem):
    """A menu item that provides title minimum rating preferences.

    :cvar fsm_key: It is a key by which the menu state is stored
        in the FSM context data.
    :cvar text: It is a static text of the menu item.

    :ivar bot: A bot that manages the menu item.
    :ivar chat: A chat, where the menu item is displayed.
    :ivar state: The FSM context.
    :ivar genre_preferences: A genre preferences manager.

    :param bot: A bot that manages the menu item.
    :param chat: A chat, where the menu item is displayed.
    :param state: The FSM context.
    :param genre_preferences: A genre preferences manager.
    """

    fsm_key = "minimum_rating"
    text = fmt.as_section(
        fmt.Underline("Minimum Rating"),
        "Set the minimum rating you want titles to have.",
    )

    async def build_keyboard(self) -> kb.InlineKeyboardMarkup:
        builder = kb.InlineKeyboardBuilder()

        current_minimum_rating = await self.genre_preferences.get_minimum_rating()

        buttons = [(f"{rating}+", rating) for rating in range(5, 10)] + [("Any", 0)]
        for text, rating in buttons:
            prefix = "✅ " if rating == current_minimum_rating else ""
            builder.button(
                text=prefix + text, callback_data=MinimumRatingCD(rating=rating)
            )

        return builder.adjust(5, 1).as_markup()

    async def build_additional_final_text(self) -> fmt.Text:
        current_minimum_rating = await self.genre_preferences.get_minimum_rating()
        return fmt.Text(
            "✅ ", f"{current_minimum_rating}+" if current_minimum_rating else "Any"
        )


def from_active_menu_item(menu_item: type[MenuItem]) -> Callable:
    """Builds a filter that allows only callback queries from the given menu item."""

    async def filter(callback_query: aiogram.types.CallbackQuery, state: FSMContext):
        expected_message_id = await state.get_value(menu_item.fsm_key)
        return callback_query.message.message_id == expected_message_id

    return filter


class SettingsMenu:
    """A wrapper that allows managing the whole menu at once."""

    def __init__(
        self,
        bot: aiogram.Bot,
        chat: aiogram.types.Chat,
        state: FSMContext,
        genre_preferences: GenrePreferences,
    ) -> None:
        self.title = TitleMenuItem(bot, chat, state, genre_preferences)
        self.title_type_selector = TitleTypeSelectorMenuItem(
            bot, chat, state, genre_preferences
        )
        self.genre_selector = GenreSelectorMenuItem(bot, chat, state, genre_preferences)
        self.genre_combinator = GenreCombinatorMenuItem(
            bot, chat, state, genre_preferences
        )
        self.minimum_rating = MinimumRatingMenuItem(bot, chat, state, genre_preferences)

        self._all = [
            self.title,
            self.title_type_selector,
            self.genre_selector,
            self.genre_combinator,
            self.minimum_rating,
        ]

    async def send(self) -> None:
        for item in self._all:
            await item.send()

    async def close(self) -> None:
        async with asyncio.TaskGroup() as tg:
            for item in self._all:
                tg.create_task(item.close())


def inject_common_objects(
    _: aiogram.types.TelegramObject,
    bot: aiogram.Bot,
    event_chat: aiogram.types.Chat,
    state: FSMContext,
    current_user: models.User,
    session: async_sa.AsyncSession,
) -> dict:
    """This filter injects ``genre_preferences`` and ``menu`` into the context.

    ``genre_preferences`` is an instance of :class:`GenrePreferences`, initialized
    with the current session and the current user.

    ``menu`` is an instance of :class:`SettingsMenu`, initialized with the current
    bot, the event chat, the FSM context and the genre preferences.
    """

    genre_preferences = GenrePreferences(session=session, user=current_user)
    return {
        "genre_preferences": genre_preferences,
        "menu": SettingsMenu(
            bot=bot,
            chat=event_chat,
            state=state,
            genre_preferences=genre_preferences,
        ),
    }


class FilterSettingsScene(Scene, state="filter_settings"):
    """At this scene, a user can adjust their filter settings.

    The scene consists of four messages:

    1. Title
    2. Genre selection preferences
    3. Genre combinator mode preferences
    4. Minimum rating preferences

    These messages are sent when a user enters the scene and called the **active menu**.
    IDs of the messages are saved for the entire duration of the scene,
    so that messages' inline keyboards can be removed when the user leaves it.
    Besides that, the scene resends its active menu when it's no longer possible
    to edit it (due to the time limit set by Telegram).
    """

    @on.message.enter()  # menu can't be injected through filters
    async def on_enter(
        self,
        message: aiogram.types.Message,
        bot: aiogram.Bot,
        event_chat: aiogram.types.Chat,
        current_user: models.User,
        session: async_sa.AsyncSession,
    ) -> None:
        """This method is called when a user enters the scene via a message.

        :param message: The message that was sent.
        :param session: A database session for this event.
        :param current_user: The user that sent the message.
        :param bot: A bot who received the event.
        :param event_chat: The chat from where the message was sent.
        """

        menu = SettingsMenu(
            bot=bot,
            chat=event_chat,
            state=self.wizard.state,
            genre_preferences=GenrePreferences(session=session, user=current_user),
        )

        await menu.send()
        logger.info("Displayed settings")

        current_user.record_settings_update()
        await session.commit()

    @on.callback_query(
        SelectGenreCD.filter(),
        from_active_menu_item(GenreSelectorMenuItem),
        inject_common_objects,
    )
    async def on_selected_genre(
        self,
        callback_query: aiogram.types.CallbackQuery,
        callback_data: SelectGenreCD,
        session: async_sa.AsyncSession,
        current_user: models.User,
        genre_preferences: GenrePreferences,
        menu: SettingsMenu,
    ) -> None:
        """This method is called when a user clicks a button with genre
        in genre selection preferences.

        :param callback_query: A callback query that was sent after the click.
        :param callback_data: Parsed callback data.
        :param session: A database session for this event.
        :param current_user: The user that clicked the button.
        :param genre_preferences: GenrePreferences object.
        :param menu: An object to manage the displayed menu.
        """

        # callback_data.selected contains a new state of the genre.
        # This way multiple clicks on the button at the same time, what
        # would normally lead to a race condition, won't lead to an unpredictable
        # sequence of genre state updates.
        if callback_data.selected:
            await genre_preferences.select_genre(callback_data.genre_id)
            logger.info(f"Selected genre id={callback_data.genre_id}")
        else:
            await genre_preferences.unselect_genre(callback_data.genre_id)
            logger.info(f"Unselected genre id={callback_data.genre_id}")

        await session.commit()

        await menu.genre_selector.update()

        current_user.record_settings_update()
        await session.commit()

    @on.callback_query(
        SelectAllGenresCD.filter(),
        from_active_menu_item(GenreSelectorMenuItem),
        inject_common_objects,
    )
    async def on_select_all_genres(
        self,
        callback_query: aiogram.types.CallbackQuery,
        callback_data: SelectAllGenresCD,
        session: async_sa.AsyncSession,
        current_user: models.User,
        genre_preferences: GenrePreferences,
        menu: SettingsMenu,
    ) -> None:
        """This method is called when a user clicks a button to select all genres
        in genre selection preferences.

        :param callback_query: A callback query that was sent after the click.
        :param callback_data: Parsed callback data.
        :param session: A database session for this event.
        :param current_user: The user that clicked the button.
        :param genre_preferences: GenrePreferences object.
        :param menu: An object to manage the displayed menu.
        """

        # callback_data.selected contains a new state.
        if callback_data.selected:
            await genre_preferences.select_all_genres()
            logger.info("Selected all genres")
        else:
            await genre_preferences.unselect_all_genres()
            logger.info("Unselected all genres")

        await session.commit()

        await menu.genre_selector.update()

        current_user.record_settings_update()
        await session.commit()

    @on.callback_query(
        SetGenreCombinatorModeCD.filter(),
        from_active_menu_item(GenreCombinatorMenuItem),
        inject_common_objects,
    )
    async def on_set_genre_combinator_mode(
        self,
        callback_query: aiogram.types.CallbackQuery,
        callback_data: SetGenreCombinatorModeCD,
        session: async_sa.AsyncSession,
        current_user: models.User,
        genre_preferences: GenrePreferences,
        menu: SettingsMenu,
    ) -> None:
        """This method is called when a user clicks a button to change genre combinator
        mode in genre combinator preferences.

        :param callback_query: A callback query that was sent after the click.
        :param callback_data: Parsed callback data.
        :param session: A database session for this event.
        :param current_user: The user that clicked the button.
        :param genre_preferences: GenrePreferences object.
        :param menu: An object to manage the displayed menu.
        """
        # callback_data.require_all contains a new state.
        if callback_data.require_all:
            await genre_preferences.require_all_selected_genres()
            logger.info("Require all selected genres")
        else:
            await genre_preferences.require_one_selected_genre()
            logger.info("Require one selected genre")
        await session.commit()

        await menu.genre_combinator.update()

        current_user.record_settings_update()
        await session.commit()

    @on.callback_query(
        MinimumRatingCD.filter(),
        from_active_menu_item(MinimumRatingMenuItem),
        inject_common_objects,
    )
    async def on_set_min_rating(
        self,
        callback_query: aiogram.types.CallbackQuery,
        callback_data: MinimumRatingCD,
        session: async_sa.AsyncSession,
        current_user: models.User,
        genre_preferences: GenrePreferences,
        menu: SettingsMenu,
    ) -> None:
        """This method is called when a user clicks a button to change
        the minimum rating.

        :param callback_query: A callback query that was sent after the click.
        :param callback_data: Parsed callback data.
        :param session: A database session for this event.
        :param current_user: The user that clicked the button.
        :param genre_preferences: GenrePreferences object.
        :param menu: An object to manage the displayed menu.
        """

        await genre_preferences.set_minimum_rating(callback_data.rating)
        await session.commit()

        await menu.minimum_rating.update()
        logger.info(f"Set minimum rating to {callback_data.rating}")

        current_user.record_settings_update()
        await session.commit()

    @on.callback_query(
        SelectTitleTypeCD.filter(),
        from_active_menu_item(TitleTypeSelectorMenuItem),
        inject_common_objects,
    )
    async def on_selected_title_type(
        self,
        callback_query: aiogram.types.CallbackQuery,
        callback_data: SelectTitleTypeCD,
        session: async_sa.AsyncSession,
        current_user: models.User,
        genre_preferences: GenrePreferences,
        menu: SettingsMenu,
    ) -> None:
        """This method is called when a user clicks a button with genre
        in genre selection preferences.

        :param callback_query: A callback query that was sent after the click.
        :param callback_data: Parsed callback data.
        :param session: A database session for this event.
        :param current_user: The user that clicked the button.
        :param genre_preferences: GenrePreferences object.
        :param menu: An object to manage the displayed menu.
        """

        # callback_data.selected contains a new state of the genre.
        if callback_data.selected:
            await genre_preferences.select_title_type(callback_data.title_type)
            logger.info(f"Selected title_type={callback_data.title_type}")
        else:
            await genre_preferences.unselect_title_type(callback_data.title_type)
            logger.info(f"Unselected title_type={callback_data.title_type}")

        await session.commit()

        await menu.title_type_selector.update()

        current_user.record_settings_update()
        await session.commit()

    @on.message(aiogram.F.text == CLOSE_SETTINGS_BTN)
    async def on_close(self, message: aiogram.types.Message):
        """This method is called when a user sends a message with
        text :attr:`CLOSE_SETTINGS_BTN` and it simply leaves the scene

        :param message: The message that was sent.
        """

        logger.debug("Closing settings")
        await self.wizard.back()

    @on.message.leave()  # menu can't be injected through filters
    async def on_leave(
        self,
        message: aiogram.types.Message,
        bot: aiogram.Bot,
        event_chat: aiogram.types.Chat,
        current_user: models.User,
        session: async_sa.AsyncSession,
    ) -> None:
        """This method is called when a user leaves the scene using a text message.

        Currently, this can be triggered by /start command or by :meth:`on_close`
        handler.

        :param message: The message that was sent.
        :param bot: A bot who received the event.
        :param event_chat: The chat, from where the event came from.
        :param current_user: The user that sent the message.
        :param session: A database session for this event.
        """

        logger.debug("Leaving settings")

        menu = SettingsMenu(
            bot=bot,
            chat=event_chat,
            state=self.wizard.state,
            genre_preferences=GenrePreferences(session=session, user=current_user),
        )
        await menu.close()

        await self.wizard.clear_data()
        logger.info("Leaved settings")
