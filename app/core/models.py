from __future__ import annotations

import datetime
import typing

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async
import sqlalchemy.orm as orm


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
        default_factory=lambda: datetime.datetime.now()  # a workaround for testing
    )
    last_activity_at: orm.Mapped[datetime.datetime] = orm.mapped_column(
        default_factory=lambda: datetime.datetime.now()  # a workaround for testing
    )
    finished_first_setup: orm.Mapped[bool] = orm.mapped_column(default=False)

    minimum_movie_rating: orm.Mapped[int] = orm.mapped_column(
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

    def update_last_activity(self) -> None:
        """Update the last activity timestamp to be the current timestamp."""
        self.last_activity_at = datetime.datetime.now()

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
