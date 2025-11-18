from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domains.family import family_schemas, family_services
from app.core.security import get_current_user
from app.domains.auth.user_models import User

router = APIRouter(prefix="/api/family", tags=["Family"])


@router.post("", status_code=201, response_model=family_schemas.UserInfo)
def add_family_member_router(
    member_in: family_schemas.FamilyMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return family_services.add_family_member(db=db, user=current_user, member_email=member_in.email)


@router.get("", response_model=family_schemas.FamilyMemberList)
def get_family_members_router(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return family_services.get_family_members(db=db, user=current_user)


@router.delete("/{member_id}", status_code=204)
def remove_family_member_router(
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    family_services.remove_family_member(db=db, user_id=current_user.id, member_id_to_remove=member_id)
    return {"message": "Family member removed successfully"}