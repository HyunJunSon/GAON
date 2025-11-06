from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from .services import ConversationFileService
from .schemas import ConversationFileResponse, FileUploadResponse, ConversationAnalysisResponse

router = APIRouter(prefix="/api", tags=["conversations"])


@router.post("/conversations/analyze", response_model=FileUploadResponse)
async def upload_conversation_file(
    user_id: int,  # TODO: JWT에서 추출하도록 수정
    family_id: int,  # TODO: JWT에서 추출하거나 파라미터로 받기
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """대화 파일 업로드 및 분석 - 새 conversation 생성"""
    service = ConversationFileService(db)
    
    try:
        conversation, db_file = await service.upload_file_and_create_conversation(user_id, family_id, file)
        
        return FileUploadResponse(
            message="파일이 성공적으로 업로드되고 처리되었습니다.",
            conversation_id=conversation.id,
            file_id=db_file.id,
            processing_status=db_file.processing_status,
            gcs_file_path=db_file.gcs_file_path
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


@router.get("/analysis/{conversation_id}", response_model=ConversationAnalysisResponse)
def get_conversation_analysis(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """대화 분석 결과 조회"""
    service = ConversationFileService(db)
    
    try:
        analysis_data = service.get_conversation_analysis(conversation_id)
        return ConversationAnalysisResponse(**analysis_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


@router.get("/conversations/files/{file_id}", response_model=ConversationFileResponse)
def get_conversation_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """파일 정보 조회"""
    service = ConversationFileService(db)
    return service.get_file_by_id(file_id)


@router.get("/conversations/users/{user_id}/files", response_model=List[ConversationFileResponse])
def get_user_files(
    user_id: int,
    db: Session = Depends(get_db)
):
    """사용자가 업로드한 모든 파일 조회"""
    service = ConversationFileService(db)
    return service.get_files_by_user_id(user_id)
