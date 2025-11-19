from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.core.config import settings


class ConversationFileResponse(BaseModel):
    id: int
    conversation_id: int
    gcs_file_path: str
    original_filename: str
    file_type: str
    file_size: int
    processing_status: str
    upload_date: datetime
    processed_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    """파일 업로드 응답 - 프론트엔드와 일치"""
    conversation_id: str  # UUID string으로 변경
    file_id: int
    status: str  # processing_status -> status로 변경
    message: str
    gcs_file_path: Optional[str] = None
    redirect_to: str = "conversation"  # 프론트엔드 리다이렉트 경로


class ConversationAnalysisResponse(BaseModel):
    summary: Optional[str] = None
    emotion: Optional[Dict[str, Any]] = None
    dialog: Optional[List[Dict[str, Any]]] = None
    status: str
    updated_at: Optional[datetime] = None
    score: Optional[float] = None
    confidence_score: Optional[float] = None
    feedback: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None
    style_analysis: Optional[Dict[str, Any]] = None


# 파일 업로드 설정을 settings에서 가져오는 헬퍼 함수들
def get_allowed_file_types() -> List[str]:
    """허용된 파일 형식 목록 반환"""
    return settings.allowed_file_types


def get_max_file_size() -> int:
    """최대 파일 크기 반환"""
    return settings.max_file_size
