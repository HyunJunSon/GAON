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
