from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


class FamilyCreate(BaseModel):
    name: str
    description: Optional[str] = None


class FamilyMemberAdd(BaseModel):
    email: EmailStr
    nickname: Optional[str] = None


class UserInfo(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True


class FamilyMemberInfo(BaseModel):
    id: int
    user_id: int
    nickname: Optional[str]
    role: str
    joined_at: datetime
    user: UserInfo

    class Config:
        from_attributes = True


class FamilyInfo(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    is_active: bool
    created_at: datetime
    members: List[FamilyMemberInfo]

    class Config:
        from_attributes = True


class FamilyList(BaseModel):
    families: List[FamilyInfo]


class SpeakerMappingCreate(BaseModel):
    conversation_id: str
    speaker_id: str
    family_member_id: Optional[int] = None
    display_name: str


class SpeakerMappingInfo(BaseModel):
    id: int
    conversation_id: str
    speaker_id: str
    family_member_id: Optional[int]
    display_name: str

    class Config:
        from_attributes = True


class ConversationSpeakers(BaseModel):
    conversation_id: str
    speakers: List[SpeakerMappingInfo]
