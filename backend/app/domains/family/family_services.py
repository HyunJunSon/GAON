from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.domains.family import family_crud as crud, family_schemas as schemas
from app.domains.auth.user_models import User
from typing import List


def create_family(db: Session, user: User, family_data: schemas.FamilyCreate) -> schemas.FamilyInfo:
    """새로운 가족/그룹을 생성합니다."""
    db_family = crud.create_family(
        db=db,
        name=family_data.name,
        owner_id=user.id,
        description=family_data.description
    )
    
    # 생성된 가족 정보 반환 (구성원 포함)
    return get_family_info(db, db_family.id)


def get_user_families(db: Session, user: User) -> schemas.FamilyList:
    """사용자가 속한 모든 가족/그룹을 조회합니다."""
    families = crud.get_user_families(db, user.id)
    family_infos = []
    
    for family in families:
        members = crud.get_family_members(db, family.id)
        family_info = schemas.FamilyInfo(
            id=family.id,
            name=family.name,
            description=family.description,
            owner_id=family.owner_id,
            is_active=family.is_active,
            created_at=family.created_at,
            members=[
                schemas.FamilyMemberInfo(
                    id=member.id,
                    user_id=member.user_id,
                    nickname=member.nickname,
                    role=member.role,
                    joined_at=member.joined_at,
                    user=schemas.UserInfo(
                        id=member.user.id,
                        name=member.user.name,
                        email=member.user.email
                    )
                ) for member in members
            ]
        )
        family_infos.append(family_info)
    
    return schemas.FamilyList(families=family_infos)


def get_family_info(db: Session, family_id: int) -> schemas.FamilyInfo:
    """특정 가족/그룹의 상세 정보를 조회합니다."""
    family = crud.get_family_by_id(db, family_id)
    if not family:
        raise HTTPException(status_code=404, detail="가족/그룹을 찾을 수 없습니다.")
    
    members = crud.get_family_members(db, family_id)
    
    return schemas.FamilyInfo(
        id=family.id,
        name=family.name,
        description=family.description,
        owner_id=family.owner_id,
        is_active=family.is_active,
        created_at=family.created_at,
        members=[
            schemas.FamilyMemberInfo(
                id=member.id,
                user_id=member.user_id,
                nickname=member.nickname,
                role=member.role,
                joined_at=member.joined_at,
                user=schemas.UserInfo(
                    id=member.user.id,
                    name=member.user.name,
                    email=member.user.email
                )
            ) for member in members
        ]
    )


def add_family_member(db: Session, user: User, family_id: int, member_data: schemas.FamilyMemberAdd) -> schemas.FamilyMemberInfo:
    """가족/그룹에 구성원을 추가합니다."""
    # 가족/그룹 존재 확인
    family = crud.get_family_by_id(db, family_id)
    if not family:
        raise HTTPException(status_code=404, detail="가족/그룹을 찾을 수 없습니다.")
    
    # 권한 확인 (owner 또는 admin만 추가 가능)
    user_member = crud.get_family_member(db, family_id, user.id)
    if not user_member or user_member.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="구성원을 추가할 권한이 없습니다.")
    
    # 추가할 사용자 조회
    member_to_add = crud.get_user_by_email(db, member_data.email)
    if not member_to_add:
        raise HTTPException(status_code=404, detail="해당 이메일을 가진 사용자가 존재하지 않습니다.")
    
    # 이미 구성원인지 확인
    existing_member = crud.get_family_member(db, family_id, member_to_add.id)
    if existing_member:
        raise HTTPException(status_code=400, detail="이미 가족/그룹 구성원입니다.")
    
    # 구성원 추가
    db_member = crud.add_family_member(
        db=db,
        family_id=family_id,
        user_id=member_to_add.id,
        nickname=member_data.nickname
    )
    
    return schemas.FamilyMemberInfo(
        id=db_member.id,
        user_id=db_member.user_id,
        nickname=db_member.nickname,
        role=db_member.role,
        joined_at=db_member.joined_at,
        user=schemas.UserInfo(
            id=member_to_add.id,
            name=member_to_add.name,
            email=member_to_add.email
        )
    )


def remove_family_member(db: Session, user: User, family_id: int, member_id: int):
    """가족/그룹에서 구성원을 제거합니다."""
    # 가족/그룹 존재 확인
    family = crud.get_family_by_id(db, family_id)
    if not family:
        raise HTTPException(status_code=404, detail="가족/그룹을 찾을 수 없습니다.")
    
    # 권한 확인 (owner, admin, 또는 본인만 제거 가능)
    user_member = crud.get_family_member(db, family_id, user.id)
    if not user_member:
        raise HTTPException(status_code=403, detail="가족/그룹 구성원이 아닙니다.")
    
    # 제거할 구성원 확인
    member_to_remove = crud.get_family_member(db, family_id, member_id)
    if not member_to_remove:
        raise HTTPException(status_code=404, detail="해당 구성원을 찾을 수 없습니다.")
    
    # 권한 체크
    if user_member.role not in ["owner", "admin"] and user.id != member_id:
        raise HTTPException(status_code=403, detail="구성원을 제거할 권한이 없습니다.")
    
    # owner는 제거할 수 없음
    if member_to_remove.role == "owner":
        raise HTTPException(status_code=400, detail="그룹 소유자는 제거할 수 없습니다.")
    
    # 구성원 제거
    success = crud.remove_family_member(db, family_id, member_id)
    if not success:
        raise HTTPException(status_code=400, detail="구성원 제거에 실패했습니다.")


def create_speaker_mapping(db: Session, mapping_data: schemas.SpeakerMappingCreate) -> schemas.SpeakerMappingInfo:
    """화자 매핑을 생성/업데이트합니다."""
    db_mapping = crud.update_speaker_mapping(
        db=db,
        conversation_id=mapping_data.conversation_id,
        speaker_id=mapping_data.speaker_id,
        family_member_id=mapping_data.family_member_id,
        display_name=mapping_data.display_name
    )
    
    return schemas.SpeakerMappingInfo(
        id=db_mapping.id,
        conversation_id=db_mapping.conversation_id,
        speaker_id=db_mapping.speaker_id,
        family_member_id=db_mapping.family_member_id,
        display_name=db_mapping.display_name
    )


def get_conversation_speakers(db: Session, conversation_id: str) -> schemas.ConversationSpeakers:
    """대화의 화자 매핑을 조회합니다."""
    speakers = crud.get_conversation_speakers(db, conversation_id)
    
    return schemas.ConversationSpeakers(
        conversation_id=conversation_id,
        speakers=[
            schemas.SpeakerMappingInfo(
                id=speaker.id,
                conversation_id=speaker.conversation_id,
                speaker_id=speaker.speaker_id,
                family_member_id=speaker.family_member_id,
                display_name=speaker.display_name
            ) for speaker in speakers
        ]
    )


# 프론트엔드용 간단한 API 함수들
def get_my_family_members(db: Session, user: User) -> schemas.SimpleFamilyResponse:
    """현재 사용자의 기본 가족 구성원 조회"""
    families = get_user_families(db, user)
    if not families.families:
        # 기본 가족이 없으면 생성
        default_family = create_family(db, user, schemas.FamilyCreate(name=f"{user.name}의 가족"))
        return schemas.SimpleFamilyResponse(members=[
            schemas.FamilyMemberSimple(
                id=str(member.id),
                name=member.user.name,
                email=member.user.email,
                joinedAt=member.joined_at.isoformat() if member.joined_at else None
            ) for member in default_family.members
        ])
    
    # 첫 번째 가족의 구성원 반환
    first_family = families.families[0]
    return schemas.SimpleFamilyResponse(members=[
        schemas.FamilyMemberSimple(
            id=str(member.id),
            name=member.user.name,
            email=member.user.email,
            joinedAt=member.joined_at.isoformat() if member.joined_at else None
        ) for member in first_family.members
    ])


def add_my_family_member(db: Session, user: User, member_data: schemas.SimpleMemberAdd) -> schemas.FamilyMemberSimple:
    """현재 사용자의 기본 가족에 구성원 추가 (알림 기반 초대)"""
    families = get_user_families(db, user)
    if not families.families:
        # 기본 가족이 없으면 생성
        default_family = create_family(db, user, schemas.FamilyCreate(name=f"{user.name}의 가족"))
        family_id = default_family.id
    else:
        family_id = families.families[0].id
    
    # 초대할 사용자 확인
    target_user = crud.get_user_by_email(db, member_data.email)
    if not target_user:
        raise HTTPException(status_code=404, detail="해당 이메일을 가진 사용자가 존재하지 않습니다.")
    
    # 이미 구성원인지 확인
    existing_member = crud.get_family_member(db, family_id, target_user.id)
    if existing_member:
        raise HTTPException(status_code=400, detail="이미 가족 구성원입니다.")
    
    # 일단 바로 추가 (나중에 초대 승인 시스템으로 개선)
    # TODO: 여기서 알림을 보내고 승인 대기 상태로 만들 수 있음
    added_member = add_family_member(
        db, user, family_id, 
        schemas.FamilyMemberAdd(email=member_data.email)
    )
    
    # 알림 데이터 생성 (프론트엔드에서 처리)
    # WebSocket이나 다른 방식으로 실시간 알림 전송 가능
    
    return schemas.FamilyMemberSimple(
        id=str(added_member.id),
        name=added_member.user.name,
        email=added_member.user.email,
        joinedAt=added_member.joined_at.isoformat() if added_member.joined_at else None
    )
