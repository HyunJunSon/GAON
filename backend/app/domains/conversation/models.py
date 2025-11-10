from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.domains.family.models import Family

# Many-to-Many 중간 테이블
user_conversations = Table(
    'user_conversations',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('conversation_id', Integer, ForeignKey('conversation.id'), primary_key=True)
)


class Conversation(Base):
    __tablename__ = "conversation"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text)
    family_id = Column(Integer, ForeignKey("family.id"))
    create_date = Column(DateTime, nullable=False)
    
    # Relationships
    participants = relationship("User", secondary=user_conversations, back_populates="conversations")
    family = relationship("Family", back_populates="conversations")
    files = relationship("ConversationFile", back_populates="conversation", cascade="all, delete-orphan")