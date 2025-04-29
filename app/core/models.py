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
        Max length is `MAX_NAME_LENGTH` (64) characters.
    :var last_name: Optional. The last name of the user.
        Max length is `MAX_NAME_LENGTH` (64) characters.
    :var username: Optional. The username of the user.
        Max length is `MAX_USERNAME_LENGTH` (32) characters.
    :var created_at: A timestamp of the first user interaction with the bot.
        Defaults to the current timestamp.
    :var last_activity_at: A timestamp of the last user interaction with the bot.
        Defaults to the current timestamp.
    """

    __tablename__ = "user"

    MAX_USERNAME_LENGTH: typing.ClassVar[int] = 32
    MAX_NAME_LENGTH: typing.ClassVar[int] = 64
    MAX_REFLINK_PARAM_LENGTH: typing.ClassVar[int] = 8

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

    def update_last_activity(self) -> None:
        """Update the last activity timestamp to be the current timestamp."""
        self.last_activity_at = datetime.datetime.now()


class Genre(Base, unsafe_hash=True):
    MAX_NAME_LENGTH: typing.ClassVar[int] = 50

    id: orm.Mapped[int] = orm.mapped_column(primary_key=True, init=False)
    name: orm.Mapped[str] = orm.mapped_column(
        sa.String(MAX_NAME_LENGTH), index=True, unique=True
    )


class TitleType(Base, unsafe_hash=True):
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


class Title(Base):
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
        secondary=title_genre_table, lazy="selectin"
    )
