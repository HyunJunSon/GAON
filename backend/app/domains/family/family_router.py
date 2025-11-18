from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domains.family import family_schemas, family_services
from app.core.security import get_current_user
from app.domains.auth.user_models import User

router = APIRouter(prefix="/api/family", tags=["Family"])


# Family 관리
@router.post("", status_code=201, response_model=family_schemas.FamilyInfo)
def create_family(
    family_data: family_schemas.FamilyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """새로운 가족/그룹을 생성합니다."""
    return family_services.create_family(db=db, user=current_user, family_data=family_data)


@router.get("", response_model=family_schemas.FamilyList)
def get_user_families(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """사용자가 속한 모든 가족/그룹을 조회합니다."""
    return family_services.get_user_families(db=db, user=current_user)


@router.get("/{family_id}", response_model=family_schemas.FamilyInfo)
def get_family_info(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """특정 가족/그룹의 상세 정보를 조회합니다."""
    return family_services.get_family_info(db=db, family_id=family_id)


# Family Member 관리
@router.post("/{family_id}/members", status_code=201, response_model=family_schemas.FamilyMemberInfo)
def add_family_member(
    family_id: int,
    member_data: family_schemas.FamilyMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """가족/그룹에 구성원을 추가합니다."""
    return family_services.add_family_member(
        db=db, user=current_user, family_id=family_id, member_data=member_data
    )


@router.delete("/{family_id}/members/{member_id}", status_code=204)
def remove_family_member(
    family_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """가족/그룹에서 구성원을 제거합니다."""
    family_services.remove_family_member(
        db=db, user=current_user, family_id=family_id, member_id=member_id
    )
    return {"message": "구성원이 성공적으로 제거되었습니다."}


# Speaker Mapping 관리
@router.post("/speakers", status_code=201, response_model=family_schemas.SpeakerMappingInfo)
def create_speaker_mapping(
    mapping_data: family_schemas.SpeakerMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """화자 매핑을 생성/업데이트합니다."""
    return family_services.create_speaker_mapping(db=db, mapping_data=mapping_data)


@router.get("/speakers/{conversation_id}", response_model=family_schemas.ConversationSpeakers)
def get_conversation_speakers(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """대화의 화자 매핑을 조회합니다."""
    return family_services.get_conversation_speakers(db=db, conversation_id=conversation_id)
