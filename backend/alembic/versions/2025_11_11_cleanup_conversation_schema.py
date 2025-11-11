"""cleanup conversation schema

Revision ID: cleanup_conv_001
Revises: 2025_11_10_086f6d0bc99a
Create Date: 2025-11-11 21:08:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'cleanup_conv_001'
down_revision = '2025_11_11_audio_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # user_conversations 테이블 정리
    op.drop_constraint('user_conversations_pkey', 'user_conversations', type_='primary')
    op.drop_column('user_conversations', 'conversation_id')
    op.alter_column('user_conversations', 'conv_id', nullable=False)
    op.create_primary_key('user_conversations_pkey', 'user_conversations', ['user_id', 'conv_id'])
    
    # practice_session 테이블에 conversation_id가 있다면 제거
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='practice_session' AND column_name='conversation_id'
    """))
    
    if result.fetchone():
        op.drop_column('practice_session', 'conversation_id')


def downgrade() -> None:
    op.drop_constraint('user_conversations_pkey', 'user_conversations', type_='primary')
    op.add_column('user_conversations', sa.Column('conversation_id', sa.Integer(), nullable=True))
    op.alter_column('user_conversations', 'conv_id', nullable=True)
    
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE user_conversations SET conversation_id = 1"))
    
    op.alter_column('user_conversations', 'conversation_id', nullable=False)
    op.create_primary_key('user_conversations_pkey', 'user_conversations', ['user_id', 'conversation_id'])
