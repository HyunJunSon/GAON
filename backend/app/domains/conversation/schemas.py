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
    message: str
    conversation_id: int
    file_id: int
    processing_status: str
    gcs_file_path: str


class ConversationAnalysisResponse(BaseModel):
    summary: str
    emotion: Dict[str, Any]
    dialog: List[Dict[str, Any]]
    status: str
    updated_at: datetime


# 파일 업로드 설정을 settings에서 가져오는 헬퍼 함수들
def get_allowed_file_types() -> List[str]:
    """허용된 파일 형식 목록 반환"""
    return settings.allowed_file_types


def get_max_file_size() -> int:
    """최대 파일 크기 반환"""
    return settings.max_file_size
