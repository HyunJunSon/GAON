from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.domains.conversation.models import Conversation


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    create_date = Column(DateTime, nullable=False)
    terms_agreed = Column(Boolean, nullable=False)
    
    # Relationships 
    conversations = relationship("Conversation", back_populates="user")