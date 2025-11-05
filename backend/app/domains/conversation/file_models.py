from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ConversationFile(Base):
    __tablename__ = "conversation_file"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversation.id", ondelete="CASCADE"))
    gcs_file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    processing_status = Column(String(20), default="pending")
    raw_content = Column(Text)
    chunked_content = Column(JSON)
    upload_date = Column(DateTime, default=func.now())
    processed_date = Column(DateTime)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="files")
