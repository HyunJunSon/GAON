"""add_status_to_family_members

Revision ID: 2687d42f5bc6
Revises: 84a14c869175
Create Date: 2025-11-19 09:14:10.413497

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2687d42f5bc6'
down_revision = '84a14c869175'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # family_members 테이블에 status 컬럼 추가 (존재하지 않을 경우에만)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    columns = [col['name'] for col in inspector.get_columns('family_members')]
    
    if 'status' not in columns:
        op.add_column('family_members', sa.Column('status', sa.String(length=20), nullable=False, server_default='active'))


def downgrade() -> None:
    # status 컬럼 제거
    op.drop_column('family_members', 'status')