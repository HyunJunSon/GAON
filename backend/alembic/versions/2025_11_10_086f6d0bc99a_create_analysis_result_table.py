"""Create analysis_result table

Revision ID: 086f6d0bc99a
Revises: be99d0c2f06d
Create Date: 2025-11-10 17:11:13.338543

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '086f6d0bc99a'
down_revision = 'be99d0c2f06d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    analysis_result 테이블 생성
    - 대화 분석 결과를 저장하는 테이블
    """
    op.create_table(
        'analysis_result',
        sa.Column('analysis_id', UUID(as_uuid=True), primary_key=True, nullable=False, comment='분석 결과 고유 ID'),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False, comment='사용자 ID'),
        sa.Column('conv_id', UUID(as_uuid=True), nullable=False, comment='대화 ID (conversation 테이블 참조)'),
        sa.Column('statistics', JSONB, nullable=True, comment='대화 통계 정보 (단어 수, 문장 수 등)'),
        sa.Column('style_analysis', JSONB, nullable=True, comment='대화 스타일 분석 결과'),
        sa.Column('conversation_count', sa.Integer, nullable=True, comment='대화 턴 수'),
        sa.Column('score', sa.Double, nullable=True, comment='대화 점수'),
        sa.Column('summary', sa.Text, nullable=True, comment='대화 요약'),
        sa.Column('confidence_score', sa.Double, nullable=True, comment='신뢰도 점수'),
        sa.Column('feedback', sa.Text, nullable=True, comment='피드백'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='생성 시각'),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='수정 시각'),
        comment='대화 분석 결과 저장 테이블'
    )
    
    # 인덱스 생성 (검색 성능 향상)
    op.create_index('idx_analysis_result_user_id', 'analysis_result', ['user_id'])
    op.create_index('idx_analysis_result_conv_id', 'analysis_result', ['conv_id'])
    op.create_index('idx_analysis_result_created_at', 'analysis_result', ['created_at'])


def downgrade() -> None:
    """
    analysis_result 테이블 삭제 (롤백)
    """
    # 인덱스 먼저 삭제
    op.drop_index('idx_analysis_result_created_at', table_name='analysis_result')
    op.drop_index('idx_analysis_result_conv_id', table_name='analysis_result')
    op.drop_index('idx_analysis_result_user_id', table_name='analysis_result')
    
    # 테이블 삭제
    op.drop_table('analysis_result')