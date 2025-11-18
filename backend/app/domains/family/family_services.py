from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.domains.family import family_crud as crud, family_schemas as schemas
from app.domains.auth.user_models import User


def add_family_member(db: Session, user: User, member_email: str) -> User:
    """
    가족 구성원을 추가합니다.
    - 자기 자신은 추가할 수 없습니다.
    - 존재하지 않는 사용자는 추가할 수 없습니다.
    - 이미 추가된 사용자는 추가할 수 없습니다.
    성공 시 추가된 사용자 정보를 반환합니다.
    """
    if user.email == member_email:
        raise HTTPException(status_code=400, detail="자기 자신을 가족 구성원으로 추가할 수 없습니다.")

    member_to_add = crud.get_user_by_email(db, email=member_email)
    if not member_to_add:
        raise HTTPException(status_code=404, detail="해당 이메일을 가진 사용자가 존재하지 않습니다.")

    existing_member = crud.get_family_member(db, user_id=user.id, member_id=member_to_add.id)
    if existing_member:
        raise HTTPException(status_code=400, detail="이미 가족 구성원으로 추가된 사용자입니다.")

    crud.add_family_member(db, user_id=user.id, member_id=member_to_add.id)
    
    # 추가된 사용자 정보를 반환
    return member_to_add


def get_family_members(db: Session, user: User) -> schemas.FamilyMemberList:
    """사용자의 가족 구성원 목록을 조회합니다."""
    members = crud.get_family_members(db, user_id=user.id)
    return schemas.FamilyMemberList(members=members)


def remove_family_member(db: Session, user_id: int, member_id_to_remove: int):
    """가족 구성원을 삭제합니다."""
    # 본인만 삭제할 수 있도록 user_id를 사용
    crud.remove_family_member(db, user_id=user_id, member_id_to_remove=member_id_to_remove)
