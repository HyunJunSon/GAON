from pydantic import BaseModel, EmailStr
from typing import List

class FamilyMemberCreate(BaseModel):
    email: EmailStr

class UserInfo(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True

class FamilyMemberList(BaseModel):
    members: List[UserInfo]
