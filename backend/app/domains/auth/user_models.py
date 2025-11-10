from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    terms_agreed = Column(Boolean, nullable=False)
    create_date = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships 
    conversations = relationship("Conversation", secondary="user_conversations", back_populates="participants")