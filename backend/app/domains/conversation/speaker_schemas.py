from pydantic import BaseModel
from typing import Dict, Optional, List
from uuid import UUID


class SpeakerMappingRequest(BaseModel):
    """화자 매핑 요청 스키마"""
    speaker_mapping: Dict[str, str]  # {"0": "아빠", "1": "딸"}
    user_mapping: Optional[Dict[str, int]] = None  # {"0": 123, "1": 456} - 스피커별 사용자 ID


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


class ManualSpeakerAssignment(BaseModel):
    """수동 화자 할당 요청"""
    segment_assignments: List[Dict[str, int]]  # [{"segment_index": 0, "speaker": 1}, ...]


class SpeakerSplitRequest(BaseModel):
    """화자 분리 개선 요청"""
    split_method: str  # "time_based", "manual", "pattern_based"
    split_interval: Optional[float] = 30.0  # 시간 기반 분리 간격 (초)
    manual_assignments: Optional[List[Dict]] = None  # 수동 할당
