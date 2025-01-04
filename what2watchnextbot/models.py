import enum
import typing

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_async
import sqlalchemy.orm as orm


class Base(orm.DeclarativeBase, sa_async.AsyncAttrs):
    """A base class for all models.

    It provides all models with a ``__tablename__`` that is a lower-cased
    name of the class, custom metadata with the predefined naming conventions
    and a :func:``_repr`` helper method that allows writing less painful
    object representations.

    It also inherits :class:`sa_async.AsyncAttrs` mixin that provides
    :attr:`awaitable_attr` for async lazy-loading in relationships.
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

    def __repr__(self) -> str:
        return self._repr(id=self.id)

    def _repr(self, **fields: typing.Unpack[dict[str, typing.Any]]) -> str:
        """A helper for __repr__

        The code is taken from the `Stackoverflow answer
        <https://stackoverflow.com/questions/55713664/sqlalchemy-best-way-to-define-repr-for-large-tables>`_
        """
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f"{key}={field!r}")
            except orm.exc.DetachedInstanceError:
                field_strings.append(f"{key}=<detached instance>")
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"{self.__class__.__name__}({', '.join(field_strings)})"
        return f"<{self.__class__.__name__} {id(self)}>"


class TitleTypes(enum.Enum):
    MOVIE = enum.auto()
    SERIES = enum.auto()
    MINI_SERIES = enum.auto()


genre_title_table = sa.Table(
    "genre_title_table",
    Base.metadata,
    sa.Column("genre_id", sa.Integer, sa.ForeignKey("genre.id"), primary_key=True),
    sa.Column("title_id", sa.Integer, sa.ForeignKey("title.id"), primary_key=True),
)


class Genre(Base):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    name: orm.Mapped[str] = orm.mapped_column(index=True, unique=True)

    titles: orm.Mapped[list["Title"]] = orm.relationship(
        secondary=genre_title_table, back_populates="genres"
    )

    def __repr__(self) -> str:
        return self._repr(id=self.id, name=self.name)


class Title(Base):
    id: orm.Mapped[int] = orm.mapped_column(primary_key=True)
    title: orm.Mapped[str]
    type: orm.Mapped[TitleTypes]
    start_year: orm.Mapped[int] = orm.mapped_column(index=True)
    end_year: orm.Mapped[int | None]
    rating: orm.Mapped[float] = orm.mapped_column(index=True)
    votes: orm.Mapped[int] = orm.mapped_column(index=True)
    genres: orm.Mapped[set["Genre"]] = orm.relationship(
        secondary=genre_title_table, back_populates="titles"
    )

    def __repr__(self) -> str:
        return self._repr(
            id=self.id,
            title=self.title,
            type=self.type,
            start_year=self.start_year,
            end_year=self.end_year,
            rating=self.rating,
            votes=self.votes,
        )

    @property
    def imdb_id(self) -> str:
        return f"tt{self.id:0>7}"

    @property
    def imdb_url(self) -> str:
        return f"https://www.imdb.com/title/{self.imdb_id}"


selected_genres_tabel = sa.Table(
    "selected_genres",
    Base.metadata,
    sa.Column("genre_id", sa.Integer, sa.ForeignKey("genre.id"), primary_key=True),
    sa.Column("user_id", sa.BigInteger, sa.ForeignKey("user.id"), primary_key=True),
)


class User(Base):
    id: orm.Mapped[int] = orm.mapped_column(sa.BigInteger, primary_key=True)
    selected_genres: orm.Mapped[set[Genre]] = orm.relationship(
        secondary=selected_genres_tabel
    )
