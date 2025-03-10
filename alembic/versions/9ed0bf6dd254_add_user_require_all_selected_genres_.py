"""Add User.require_all_selected_genres field

Revision ID: 9ed0bf6dd254
Revises: 72e8938336f5
Create Date: 2025-01-05 22:28:14.362945

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9ed0bf6dd254"
down_revision: Union[str, None] = "72e8938336f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user",
        sa.Column(
            "require_all_selected_genres",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user", "require_all_selected_genres")
    # ### end Alembic commands ###
