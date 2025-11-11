"""create new ideal_answer table schema

Revision ID: new_ideal_answer
Revises: be99d0c2f06d
Create Date: 2025-11-11 13:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = 'new_ideal_answer'
down_revision = 'be99d0c2f06d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing ideal_answer table if exists
    op.execute("DROP TABLE IF EXISTS ideal_answer CASCADE")
    
    # Create new ideal_answer table with updated schema
    op.create_table('ideal_answer',
        sa.Column('snippet_id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('book_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('book_title', sa.Text(), nullable=True),
        sa.Column('l1_title', sa.Text(), nullable=True),
        sa.Column('l2_title', sa.Text(), nullable=True),
        sa.Column('l3_title', sa.Text(), nullable=True),
        sa.Column('canonical_path', sa.Text(), nullable=True),
        sa.Column('section_id', sa.Text(), nullable=True),
        sa.Column('chunk_ix', sa.Integer(), nullable=True),
        sa.Column('page_start', sa.Integer(), nullable=True),
        sa.Column('page_end', sa.Integer(), nullable=True),
        sa.Column('citation', sa.Text(), nullable=True),
        sa.Column('full_text', sa.Text(), nullable=True),
        sa.Column('embed_text', sa.Text(), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.PrimaryKeyConstraint('snippet_id')
    )
    
    # Create indexes for better performance
    op.create_index('idx_ideal_answer_book_id', 'ideal_answer', ['book_id'])
    op.create_index('idx_ideal_answer_embedding', 'ideal_answer', ['embedding'], 
                   postgresql_using='ivfflat', 
                   postgresql_ops={'embedding': 'vector_cosine_ops'},
                   postgresql_with={'lists': '100'})


def downgrade() -> None:
    # Drop new table and indexes
    op.drop_index('idx_ideal_answer_embedding', table_name='ideal_answer')
    op.drop_index('idx_ideal_answer_book_id', table_name='ideal_answer')
    op.drop_table('ideal_answer')
    
    # Recreate old ideal_answer table structure
    op.create_table('ideal_answer',
        sa.Column('idea_id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('source', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('analysisid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint('idea_id')
    )
