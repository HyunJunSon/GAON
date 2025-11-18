from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class Family(Base):
    __tablename__ = "family"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    member_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    description = Column(Text)
    create_date = Column(DateTime, nullable=False)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="family")

    __table_args__ = (
        UniqueConstraint('user_id', 'member_id', name='_user_member_uc'),
    )

class FamilyMember(Base):
    __tablename__ = 'family_members'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    member_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'member_id', name='_user_member_uc'),
    )