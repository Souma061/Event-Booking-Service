"""added oauth fields

Revision ID: 7f6d8c9b2a31
Revises: 126b25d4eb52
Create Date: 2026-04-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7f6d8c9b2a31"
down_revision: Union[str, Sequence[str], None] = "126b25d4eb52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("oauth_provider", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("oauth_sub", sa.String(length=255), nullable=True))
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    op.drop_column("users", "oauth_sub")
    op.drop_column("users", "oauth_provider")
