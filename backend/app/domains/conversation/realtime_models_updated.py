from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum


class SessionStatus(enum.Enum):
    ACTIVE = "active"
    ENDED = "ended"


class MessageType(enum.Enum):
    TEXT = "text"
    SYSTEM = "system"


class RealtimeSession(Base):
    __tablename__ = "realtime_session"

    id = Column(Integer, primary_key=True)
    room_id = Column(String, unique=True, nullable=False)
    family_id = Column(Integer, ForeignKey("family.id"), nullable=True)  # nullable로 변경
    display_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    ended_at = Column(DateTime, nullable=True)
    status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    
    # Relationships
    messages = relationship("RealtimeMessage", back_populates="session", cascade="all, delete-orphan")


class RealtimeMessage(Base):
    __tablename__ = "realtime_message"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("realtime_session.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    
    # Relationships
    session = relationship("RealtimeSession", back_populates="messages")
