"""Add Title, Genre and TitleType models

Revision ID: 8e43cbf70467
Revises: 20ef90e0583e
Create Date: 2025-04-25 13:41:01.307674

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8e43cbf70467"
down_revision: Union[str, None] = "20ef90e0583e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "genre",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_genre")),
    )
    op.create_index(op.f("ix_genre_name"), "genre", ["name"], unique=True)
    op.create_table(
        "titletype",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=15), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_titletype")),
    )
    op.create_index(op.f("ix_titletype_name"), "titletype", ["name"], unique=True)
    op.create_table(
        "title",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("type_id", sa.Integer(), nullable=False),
        sa.Column("start_year", sa.Integer(), nullable=False),
        sa.Column("end_year", sa.Integer(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=False),
        sa.Column("votes", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["type_id"], ["titletype.id"], name=op.f("fk_title_type_id_titletype")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_title")),
    )
    op.create_index(op.f("ix_title_rating"), "title", ["rating"], unique=False)
    op.create_index(op.f("ix_title_start_year"), "title", ["start_year"], unique=False)
    op.create_index(op.f("ix_title_type_id"), "title", ["type_id"], unique=False)
    op.create_index(op.f("ix_title_votes"), "title", ["votes"], unique=False)
    op.create_table(
        "title_genre",
        sa.Column("title_id", sa.Integer(), nullable=False),
        sa.Column("genre_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["genre_id"],
            ["genre.id"],
            name=op.f("fk_title_genre_genre_id_genre"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["title_id"],
            ["title.id"],
            name=op.f("fk_title_genre_title_id_title"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("title_id", "genre_id", name=op.f("pk_title_genre")),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("title_genre")
    op.drop_index(op.f("ix_title_votes"), table_name="title")
    op.drop_index(op.f("ix_title_type_id"), table_name="title")
    op.drop_index(op.f("ix_title_start_year"), table_name="title")
    op.drop_index(op.f("ix_title_rating"), table_name="title")
    op.drop_table("title")
    op.drop_index(op.f("ix_titletype_name"), table_name="titletype")
    op.drop_table("titletype")
    op.drop_index(op.f("ix_genre_name"), table_name="genre")
    op.drop_table("genre")
    # ### end Alembic commands ###
