"""merge_heads

Revision ID: e514ebe1c2f6
Revises: 086f6d0bc99a, cleanup_conv_001, new_ideal_answer
Create Date: 2025-11-18 15:12:47.465466

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e514ebe1c2f6'
down_revision = ('086f6d0bc99a', 'cleanup_conv_001', 'new_ideal_answer')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass