from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Conversation(Base):
    __tablename__ = "conversation"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    family_id = Column(Integer, ForeignKey("family.id"))
    create_date = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    family = relationship("Family", back_populates="conversations")
    files = relationship("ConversationFile", back_populates="conversation", cascade="all, delete-orphan")