from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base
from app.domains.family.models import Family

# Many-to-Many 중간 테이블
user_conversations = Table(
    'user_conversations',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('conv_id', UUID(as_uuid=True), ForeignKey('conversation.conv_id'), primary_key=True)
)


class Conversation(Base):
    __tablename__ = "conversation"

    conv_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id = Column(Integer)
    title = Column(String, nullable=False)
    content = Column(Text)
    family_id = Column(Integer, ForeignKey("family.id"))
    create_date = Column(DateTime, nullable=False)
    
    # Relationships
    participants = relationship("User", secondary=user_conversations, back_populates="conversations")
    family = relationship("Family", back_populates="conversations")
    files = relationship("ConversationFile", back_populates="conversation", cascade="all, delete-orphan")