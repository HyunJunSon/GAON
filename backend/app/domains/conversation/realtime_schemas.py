from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .realtime_models import SessionStatus, MessageType


class MessageCreate(BaseModel):
    message: str
    message_type: MessageType = MessageType.TEXT


class MessageResponse(BaseModel):
    id: int
    user_id: int
    message: str
    timestamp: datetime
    message_type: MessageType

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    room_id: str
    family_id: int


class SessionResponse(BaseModel):
    id: int
    room_id: str
    family_id: int
    created_at: datetime
    ended_at: Optional[datetime]
    status: SessionStatus

    class Config:
        from_attributes = True


class WebSocketMessage(BaseModel):
    type: str  # "message", "join", "leave", "error"
    data: dict
