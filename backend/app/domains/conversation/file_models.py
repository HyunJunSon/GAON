from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class ConversationFile(Base):
    __tablename__ = "conversation_file"

    id = Column(Integer, primary_key=True)
    conv_id = Column(UUID(as_uuid=True), ForeignKey("conversation.conv_id", ondelete="CASCADE"))
    gcs_file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    processing_status = Column(String(20), default="pending")
    raw_content = Column(Text)
    chunked_content = Column(JSON)
    upload_date = Column(DateTime, default=func.now())
    processed_date = Column(DateTime)
    
    # 음성 대화 관련 필드 추가
    audio_url = Column(String(500), nullable=True)  # GCS 오디오 파일 경로
    transcript = Column(Text, nullable=True)  # 전체 대화 텍스트
    speaker_segments = Column(JSON, nullable=True)  # 화자별 구간 정보
    duration = Column(Integer, nullable=True)  # 총 대화시간(초)
    speaker_count = Column(Integer, nullable=True)  # 참여자 수
    
    # Relationships
    conversation = relationship("Conversation", back_populates="files")
