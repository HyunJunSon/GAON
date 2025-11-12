from pydantic import BaseModel
from typing import Dict, Optional
from uuid import UUID


class SpeakerMappingRequest(BaseModel):
    """화자 매핑 요청 스키마"""
    speaker_mapping: Dict[str, str]  # {"0": "아빠", "1": "딸"}


class SpeakerMappingResponse(BaseModel):
    """화자 매핑 응답 스키마"""
    conversation_id: str
    file_id: int
    speaker_mapping: Dict[str, Optional[str]]
    message: str


class SpeakerSegmentWithMapping(BaseModel):
    """매핑된 화자 정보가 포함된 세그먼트"""
    speaker: int
    speaker_name: Optional[str]  # 매핑된 이름
    start: float
    end: float
    text: str
