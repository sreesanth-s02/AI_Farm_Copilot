"""fix created_at server default

Revision ID: 192e1305e638
Revises: 0f0aaa7e04b1
Create Date: 2026-10-04 00:36:05.373252

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '192e1305e638'
down_revision: Union[str, Sequence[str], None] = '0f0aaa7e04b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "farmers",
        "created_at",
        existing_type=sa.DateTime(),
        server_default=sa.text("CURRENT_TIMESTAMP"),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "farmers",
        "created_at",
        existing_type=sa.DateTime(),
        server_default=None,
        existing_nullable=False,
    )
