from sqlalchemy import Column, Integer, Text, DateTime, ARRAY, String
from sqlalchemy.sql import func
from app.core.database import Base


class RawConversation(Base):
    __tablename__ = "raw_conversation"

    raw_id = Column(Integer, primary_key=True)
    context = Column(Text, nullable=False)
    involve_user_id = Column(ARRAY(String), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())
