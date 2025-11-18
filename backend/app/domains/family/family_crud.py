from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.domains.family.family_models import Family, FamilyMember, SpeakerMapping
from app.domains.auth.user_models import User
from typing import List, Optional


# Family CRUD
def create_family(db: Session, name: str, owner_id: int, description: str = None) -> Family:
    """새로운 가족/그룹을 생성합니다."""
    db_family = Family(
        name=name,
        description=description,
        owner_id=owner_id
    )
    db.add(db_family)
    db.commit()
    db.refresh(db_family)
    
    # 생성자를 owner로 자동 추가
    add_family_member(db, family_id=db_family.id, user_id=owner_id, role="owner")
    
    return db_family


def get_family_by_id(db: Session, family_id: int) -> Optional[Family]:
    """ID로 가족/그룹을 조회합니다."""
    return db.query(Family).filter(Family.id == family_id, Family.is_active == True).first()


def get_user_families(db: Session, user_id: int) -> List[Family]:
    """사용자가 속한 모든 가족/그룹을 조회합니다."""
    return db.query(Family).join(FamilyMember).filter(
        FamilyMember.user_id == user_id,
        Family.is_active == True
    ).all()


def update_family(db: Session, family_id: int, name: str = None, description: str = None) -> Optional[Family]:
    """가족/그룹 정보를 업데이트합니다."""
    db_family = get_family_by_id(db, family_id)
    if not db_family:
        return None
    
    if name is not None:
        db_family.name = name
    if description is not None:
        db_family.description = description
    
    db.commit()
    db.refresh(db_family)
    return db_family


def delete_family(db: Session, family_id: int) -> bool:
    """가족/그룹을 비활성화합니다."""
    db_family = get_family_by_id(db, family_id)
    if not db_family:
        return False
    
    db_family.is_active = False
    db.commit()
    return True


# FamilyMember CRUD
def add_family_member(db: Session, family_id: int, user_id: int, nickname: str = None, role: str = "member") -> FamilyMember:
    """가족/그룹에 구성원을 추가합니다."""
    db_member = FamilyMember(
        family_id=family_id,
        user_id=user_id,
        nickname=nickname,
        role=role
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


def get_family_members(db: Session, family_id: int) -> List[FamilyMember]:
    """가족/그룹의 모든 구성원을 조회합니다."""
    return db.query(FamilyMember).filter(FamilyMember.family_id == family_id).all()


def get_family_member(db: Session, family_id: int, user_id: int) -> Optional[FamilyMember]:
    """특정 가족/그룹의 특정 구성원을 조회합니다."""
    return db.query(FamilyMember).filter(
        and_(FamilyMember.family_id == family_id, FamilyMember.user_id == user_id)
    ).first()


def remove_family_member(db: Session, family_id: int, user_id: int) -> bool:
    """가족/그룹에서 구성원을 제거합니다."""
    db_member = get_family_member(db, family_id, user_id)
    if not db_member:
        return False
    
    db.delete(db_member)
    db.commit()
    return True


def update_family_member(db: Session, family_id: int, user_id: int, nickname: str = None, role: str = None) -> Optional[FamilyMember]:
    """가족/그룹 구성원 정보를 업데이트합니다."""
    db_member = get_family_member(db, family_id, user_id)
    if not db_member:
        return None
    
    if nickname is not None:
        db_member.nickname = nickname
    if role is not None:
        db_member.role = role
    
    db.commit()
    db.refresh(db_member)
    return db_member


# User 조회
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """이메일로 사용자를 조회합니다."""
    return db.query(User).filter(User.email == email).first()


# SpeakerMapping CRUD
def create_speaker_mapping(db: Session, conversation_id: str, speaker_id: str, 
                          family_member_id: int = None, display_name: str = None) -> SpeakerMapping:
    """화자 매핑을 생성합니다."""
    db_mapping = SpeakerMapping(
        conversation_id=conversation_id,
        speaker_id=speaker_id,
        family_member_id=family_member_id,
        display_name=display_name
    )
    db.add(db_mapping)
    db.commit()
    db.refresh(db_mapping)
    return db_mapping


def get_conversation_speakers(db: Session, conversation_id: str) -> List[SpeakerMapping]:
    """대화의 모든 화자 매핑을 조회합니다."""
    return db.query(SpeakerMapping).filter(SpeakerMapping.conversation_id == conversation_id).all()


def update_speaker_mapping(db: Session, conversation_id: str, speaker_id: str, 
                          family_member_id: int = None, display_name: str = None) -> Optional[SpeakerMapping]:
    """화자 매핑을 업데이트합니다."""
    db_mapping = db.query(SpeakerMapping).filter(
        and_(SpeakerMapping.conversation_id == conversation_id, SpeakerMapping.speaker_id == speaker_id)
    ).first()
    
    if not db_mapping:
        return create_speaker_mapping(db, conversation_id, speaker_id, family_member_id, display_name)
    
    if family_member_id is not None:
        db_mapping.family_member_id = family_member_id
    if display_name is not None:
        db_mapping.display_name = display_name
    
    db.commit()
    db.refresh(db_mapping)
    return db_mapping
