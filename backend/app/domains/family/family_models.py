from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Family(Base):
    """가족/그룹 테이블"""
    __tablename__ = "family"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)  # 그룹 이름 (예: "우리 가족", "친구들")
    description = Column(Text, nullable=True)   # 그룹 설명
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # 그룹 생성자/관리자
    is_active = Column(Boolean, default=True)   # 활성 상태
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("FamilyMember", back_populates="family", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="family")


class FamilyMember(Base):
    """가족 구성원 테이블"""
    __tablename__ = 'family_members'

    id = Column(Integer, primary_key=True)
    family_id = Column(Integer, ForeignKey('family.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    nickname = Column(String(50), nullable=True)  # 그룹 내 별명 (예: "엄마", "아빠", "형")
    role = Column(String(20), default="member")   # 역할 (owner, admin, member)
    status = Column(String(20), default="active")  # 상태 (pending, active, declined)
    joined_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    family = relationship("Family", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        UniqueConstraint('family_id', 'user_id', name='_family_user_uc'),
    )


class SpeakerMapping(Base):
    """화자 매핑 테이블 - 대화 분석 시 화자와 사용자 연결"""
    __tablename__ = 'speaker_mappings'

    id = Column(Integer, primary_key=True)
    conversation_id = Column(String, nullable=False)  # 대화 ID
    speaker_id = Column(String, nullable=False)       # 화자 ID (0, 1, 2...)
    family_member_id = Column(Integer, ForeignKey('family_members.id'), nullable=True)
    display_name = Column(String(100), nullable=False)  # 표시될 이름
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    family_member = relationship("FamilyMember")

    __table_args__ = (
        UniqueConstraint('conversation_id', 'speaker_id', name='_conv_speaker_uc'),
    )
