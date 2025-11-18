"""add_rag_type_to_ideal_answer

Revision ID: 7a1414872d79
Revises: e514ebe1c2f6
Create Date: 2025-11-18 15:12:53.313109

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a1414872d79'
down_revision = 'e514ebe1c2f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add rag_type column to ideal_answer table
    op.add_column('ideal_answer', sa.Column('rag_type', sa.String(50), nullable=True))


def downgrade() -> None:
    # Remove rag_type column from ideal_answer table
    op.drop_column('ideal_answer', 'rag_type')