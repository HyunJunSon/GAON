"""Add age and gender columns to users table

Revision ID: 740afd11abfe
Revises: 7a1414872d79
Create Date: 2025-11-20 14:39:27.470553

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '740afd11abfe'
down_revision = '7a1414872d79'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('age', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('gender', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'gender')
    op.drop_column('users', 'age')