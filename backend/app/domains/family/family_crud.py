from sqlalchemy.orm import Session
from app.domains.family.family_models import FamilyMember
from app.domains.auth.user_models import User


def get_user_by_email(db: Session, email: str) -> User | None:
    """이메일로 사용자를 조회합니다."""
    return db.query(User).filter(User.email == email).first()


def get_family_members(db: Session, user_id: int) -> list[User]:
    """사용자의 모든 가족 구성원을 조회합니다."""
    return db.query(User).join(FamilyMember, User.id == FamilyMember.member_id).filter(FamilyMember.user_id == user_id).all()


def add_family_member(db: Session, user_id: int, member_id: int) -> FamilyMember:
    """새로운 가족 구성원 관계를 추가합니다."""
    db_family_member = FamilyMember(user_id=user_id, member_id=member_id)
    db.add(db_family_member)
    db.commit()
    db.refresh(db_family_member)
    return db_family_member


def get_family_member(db: Session, user_id: int, member_id: int) -> FamilyMember | None:
    """특정 가족 구성원 관계가 존재하는지 확인합니다."""
    return db.query(FamilyMember).filter(FamilyMember.user_id == user_id, FamilyMember.member_id == member_id).first()


def remove_family_member(db: Session, user_id: int, member_id_to_remove: int):
    """가족 구성원 관계를 삭제합니다."""
    db_family_member = db.query(FamilyMember).filter(
        FamilyMember.user_id == user_id,
        FamilyMember.member_id == member_id_to_remove
    ).first()

    if db_family_member:
        db.delete(db_family_member)
        db.commit()