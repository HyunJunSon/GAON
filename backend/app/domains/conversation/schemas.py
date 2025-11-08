from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# 지원하는 파일 형식 및 제한사항
ALLOWED_FILE_TYPES = {"txt", "pdf", "docx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


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
    conversation_id: int  # snake_case로 변경
    file_id: int
    status: str  # processing_status -> status로 변경
    message: str
    gcs_file_path: Optional[str] = None


class ConversationAnalysisResponse(BaseModel):
    summary: str
    emotion: Dict[str, Any]
    dialog: List[Dict[str, Any]]
    status: str
    updated_at: datetime
