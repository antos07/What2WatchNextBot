from __future__ import annotations

import datetime
import typing
from functools import cached_property

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async
import sqlalchemy.orm as orm

from app.core import constants
from app.utils import utcnow


class _AwareDateTime(sa.TypeDecorator):
    """Same as ``sa.DateTime`` but adds UTC timezone if missing."""

    impl = sa.DateTime

    def __init__(self, *args, **kwargs) -> None:
        kwargs["timezone"] = True
        super().__init__(*args, **kwargs)

    def process_bind_param[T: datetime.datetime | None](
        self, value: T, dialect: sa.Dialect
    ) -> T:
        # Ensure datetime is in UTC and timezone-aware before storing
        if value is not None and value.tzinfo is None:
            raise ValueError("Naive datetime passed to AwareDateTime")
        return value

    def process_result_value[T: datetime.datetime | None](
        self, value: T, dialect: sa.Dialect
    ) -> T:
        # Add UTC tzinfo on fetch if missing
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=datetime.UTC)
        return value


class Base(orm.MappedAsDataclass, orm.DeclarativeBase, sa_async.AsyncAttrs):
    """A base class for all models.

    It provides all models with a ``__tablename__`` that is a lower-cased
    name of the class, custom metadata with the predefined naming conventions.

    It also inherits ``sa_async.AsyncAttrs`` mixin that provides
    ``awaitable_attr`` for async lazy-loading in relationships.

    All the models should assume they are dataclasses.
    """

    __abstract__ = True

    # Default naming conventions
    metadata = sa.MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

    @orm.declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class User(Base):
    """
    A user model.

    :var id: A user identifier (usually provided by Telegram).
    :var first_name: The first name of the user.
        Max length is ``MAX_NAME_LENGTH`` (64) characters.
    :var last_name: Optional. The last name of the user.
        Max length is ``MAX_NAME_LENGTH`` (64) characters.
    :var username: Optional. The username of the user.
        Max length is ``MAX_USERNAME_LENGTH`` (32) characters.
    :var created_at: A timestamp of the first user interaction with the bot.
        Defaults to the current timestamp.
    :var last_activity_at: A timestamp of the last user interaction with the bot.
        Defaults to the current timestamp.
    :var finished_first_setup: A flag indicating whether the first setup is finished.
        Defaults to ``False``.
    :var minimum_movie_rating: The minimum movie rating selected by the user.
        Defaults to ``DEFAULT_MINIMUM_MOVIE_RATING`` (7).
    :var minimum_movie_votes: The minimum number of votes selected by the user.
        Defaults to ``DEFAULT_MINIMUM_MOVIE_VOTES`` (10000).
    :var selected_title_types: A set of selected title types.
    :var selected_genres: A set of selected genres.
    :var requires_all_selected_genres: A flag indicating whether all selected genres
        are required for the search. Defaults to ``False``.
    :var skipped_titles: A list of titles skipped by the user.
    :cvar MAX_USERNAME_LENGTH: The maximum length of the username.
    :cvar MAX_NAME_LENGTH: The maximum length of the first name and last name.
    :cvar MAX_REFLINK_PARAM_LENGTH: The maximum length of the reflink parameter.
    :cvar DEFAULT_MINIMUM_MOVIE_RATING: The default minimum movie rating.
    :cvar DEFAULT_MINIMUM_MOVIE_VOTES: The default minimum movie votes.
    """

    __tablename__ = "user"

    MAX_USERNAME_LENGTH: typing.ClassVar[int] = 32
    MAX_NAME_LENGTH: typing.ClassVar[int] = 64
    MAX_REFLINK_PARAM_LENGTH: typing.ClassVar[int] = 8

    DEFAULT_MINIMUM_MOVIE_RATING: typing.ClassVar[int] = 7
    DEFAULT_MINIMUM_MOVIE_VOTES: typing.ClassVar[int] = 10_000

    id: orm.Mapped[int] = orm.mapped_column(
        sa.BigInteger, primary_key=True, autoincrement=False
    )
    first_name: orm.Mapped[str] = orm.mapped_column(sa.String(MAX_NAME_LENGTH))
    last_name: orm.Mapped[str | None] = orm.mapped_column(
        sa.String(MAX_NAME_LENGTH), default=None
    )
    username: orm.Mapped[str | None] = orm.mapped_column(
        sa.String(MAX_USERNAME_LENGTH), default=None
    )
    created_at: orm.Mapped[datetime.datetime] = orm.mapped_column(
        _AwareDateTime,
        default_factory=lambda: utcnow(),  # a workaround for testing
    )
    last_activity_at: orm.Mapped[datetime.datetime] = orm.mapped_column(
        _AwareDateTime,
        default_factory=lambda: utcnow(),  # a workaround for testing
    )
    finished_first_setup: orm.Mapped[bool] = orm.mapped_column(default=False)

    minimum_movie_rating: orm.Mapped[float] = orm.mapped_column(
        default=DEFAULT_MINIMUM_MOVIE_RATING
    )
    minimum_movie_votes: orm.Mapped[int] = orm.mapped_column(
        default=DEFAULT_MINIMUM_MOVIE_VOTES
    )
    selected_title_types: orm.Mapped[set[TitleType]] = orm.relationship(
        secondary=lambda: user_title_type_table,
        default_factory=set,
        hash=False,
        repr=False,
    )
    selected_genres: orm.Mapped[set[Genre]] = orm.relationship(
        secondary=lambda: user_genre_table,
        default_factory=set,
        hash=False,
        repr=False,
    )
    requires_all_selected_genres: orm.Mapped[bool] = orm.mapped_column(default=False)
    skipped_titles: orm.Mapped[list[TitleSkip]] = orm.relationship(
        default_factory=list, back_populates="user"
    )

    def update_last_activity(self) -> None:
        """Update the last activity timestamp to be the current timestamp."""
        self.last_activity_at = utcnow()

    async def select_genre(self, genre: Genre) -> None:
        """Add a genre to the user's selected genres."""
        (await self.awaitable_attrs.selected_genres).add(genre)

    async def deselect_genre(self, genre: Genre) -> None:
        """Remove a genre from the user's selected genres."""
        (await self.awaitable_attrs.selected_genres).discard(genre)

    async def select_title_type(self, title_type: TitleType) -> None:
        """Add a title type to the user's selected title types."""
        (await self.awaitable_attrs.selected_title_types).add(title_type)

    async def deselect_title_type(self, title_type: TitleType) -> None:
        """Remove a title type from the user's selected title types."""
        (await self.awaitable_attrs.selected_title_types).discard(title_type)

    async def skip_title(
        self,
        title: Title,
        expires_after: datetime.timedelta = constants.SKIPPED_TITLE_TIMEOUT,
    ) -> None:
        """Skip a title."""
        skipped_titles = await self.awaitable_attrs.skipped_titles

        try:
            skip = next(
                skip
                for skip in skipped_titles
                if skip.title_id == title.id and skip.user_id == self.id
            )
        except StopIteration:
            skip = TitleSkip(title=title, user=self)
            skipped_titles.append(skip)

        skip.expires_at = utcnow() + expires_after


class Genre(Base, unsafe_hash=True):
    """
    Represents a genre entity in the database.

    This class is used to map a genre entity, containing an identifier and a
    unique name, to the database. It enforces constraints on the maximum length of
    the genre name and ensures that it is unique for efficient indexing.

    :cvar MAX_NAME_LENGTH: The maximum allowable length of the genre name.
    :var id: The unique identifier of the genre, serving as the primary key.
    :var name: The name of the genre, constrained by a maximum length, indexed,
        and required to be unique.
    """

    MAX_NAME_LENGTH: typing.ClassVar[int] = 50

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True, init=False)
    name: orm.Mapped[str] = orm.mapped_column(
        sa.String(MAX_NAME_LENGTH), index=True, unique=True
    )


class TitleType(Base, unsafe_hash=True):
    """
    Represents a TitleType entity for use in database models.

    This class defines the structure and constraints for managing
    title types within the database. The ``TitleType`` object includes
    attributes such as `id`, which uniquely identifies a title type,
    and `name`, which specifies the name of the title type, constrained
    by maximum length and uniqueness.

    :cvar MAX_NAME_LENGTH: Maximum allowed length for the name attribute.
    :var id: Unique identifier for this title type.
    :var name: Name of the title type, limited to ``MAX_NAME_LENGTH``
        characters and must be unique.
    """

    MAX_NAME_LENGTH: typing.ClassVar[int] = 15

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True, init=False)
    name: orm.Mapped[str] = orm.mapped_column(
        sa.String(MAX_NAME_LENGTH), index=True, unique=True
    )


title_genre_table = sa.Table(
    "title_genre",
    Base.metadata,
    sa.Column(
        "title_id",
        sa.Integer,
        sa.ForeignKey("title.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "genre_id",
        sa.Integer,
        sa.ForeignKey("genre.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Title(Base, unsafe_hash=True):
    """
    Represents a Title in the system.

    This class provides a way to model a title with various attributes such as a unique
    identifier, associated type, years of activity, user rating, vote count,
    and linked genres. It is intended to be used as an entity for database storage
    and retrieval using ORM.

    :var id: The unique identifier for the title.
    :var title: The name or label of the title.
    :var type_id: The foreign key linking the title to its type.
    :var type: The TitleType object associated with the title.
    :var start_year: The first year when the title was relevant or started.
    :var end_year: The last year when the title was relevant or ended.
    :var rating: The user-assigned rating for the title.
    :var votes: The count of votes received for the title.
    :var genres: The set of Genre objects associated with the title.
    """

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    title: orm.Mapped[str]
    type_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey(TitleType.id), index=True, init=False, repr=False
    )
    type: orm.Mapped[TitleType] = orm.relationship(lazy="joined")
    start_year: orm.Mapped[int] = orm.mapped_column(index=True)
    end_year: orm.Mapped[int | None]
    rating: orm.Mapped[float] = orm.mapped_column(index=True)
    votes: orm.Mapped[int] = orm.mapped_column(index=True)
    genres: orm.Mapped[set["Genre"]] = orm.relationship(
        secondary=title_genre_table, lazy="selectin", hash=False
    )

    @cached_property
    def imdb_id(self) -> str:
        return f"tt{self.id:0>7}"

    @cached_property
    def imdb_url(self) -> str:
        return f"https://www.imdb.com/title/{self.imdb_id}"


class TitleSkip(Base):
    """Represents a Title skipped by the user.

    :var title_id: The id of the title that is skipped. It's part of the primary key
        in the database, and it's a foreign key to the ``title`` table.
    :var title: The title that is skipped.
    :var user_id: The id of the user that skips the title. It's part of the primary key
        in the database, and it's a foreign key to the ``user`` table.
    :var user: The user that skips the title.
    :var is_watched: A flag indicating whether the user has watched the title.
    :var expires_at: The timestamp when the skip expires.
    """

    title_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey(Title.id), primary_key=True, init=False
    )
    title: orm.Mapped[Title] = orm.relationship(repr=False)
    user_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey(User.id), primary_key=True, init=False
    )
    user: orm.Mapped[User] = orm.relationship(
        repr=False, back_populates="skipped_titles"
    )
    is_watched: orm.Mapped[bool] = orm.mapped_column(default=False)
    expires_at: orm.Mapped[datetime.datetime | None] = orm.mapped_column(
        _AwareDateTime(), default=None
    )


user_genre_table = sa.Table(
    "user_genre",
    Base.metadata,
    sa.Column(
        "user_id",
        sa.BigInteger,
        sa.ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "genre_id",
        sa.Integer,
        sa.ForeignKey("genre.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

user_title_type_table = sa.Table(
    "user_title_type",
    Base.metadata,
    sa.Column(
        "user_id",
        sa.BigInteger,
        sa.ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    sa.Column(
        "title_type_id",
        sa.Integer,
        sa.ForeignKey("titletype.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
