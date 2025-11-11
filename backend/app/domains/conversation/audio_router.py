from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from typing import Optional
import logging
from datetime import datetime
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.user_models import User
from .stt_service import STTService
from .services import ConversationFileService
from .models import Conversation
from .file_models import ConversationFile
from .schemas import FileUploadResponse

router = APIRouter(prefix="/api/conversation", tags=["audio-conversation"])
logger = logging.getLogger(__name__)


@router.post("/audio", response_model=FileUploadResponse)
async def upload_audio_conversation(
    file: UploadFile = File(...),
    family_id: Optional[int] = Form(1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    음성 파일을 업로드하고 STT 처리를 수행합니다.
    
    Args:
        file: 업로드할 음성 파일 (WebM 형식)
        family_id: 가족 ID (기본값: 1)
        current_user: 현재 로그인한 사용자
        db: 데이터베이스 세션
        
    Returns:
        FileUploadResponse: 업로드 및 처리 결과
    """
    logger.info(f"음성 파일 업로드 요청 - 사용자: {current_user.id}, 파일: {file.filename}")
    
    try:
        # 1. 파일 유효성 검사
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        # 음성 파일 형식 확인
        file_extension = file.filename.split('.')[-1].lower()
        allowed_audio_extensions = {'webm', 'wav', 'mp3', 'm4a'}
        
        if file_extension not in allowed_audio_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 음성 파일 형식입니다. 지원 형식: {', '.join(allowed_audio_extensions)}"
            )
        
        # 2. 파일 크기 검사 (20MB 제한)
        file_content = await file.read()
        max_size = 20 * 1024 * 1024  # 20MB
        
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400, 
                detail=f"파일 크기가 너무 큽니다. 최대 크기: {max_size // (1024*1024)}MB"
            )
        
        # 3. STT 서비스 초기화 및 처리
        stt_service = STTService()
        
        # 오디오 형식 검증
        if not stt_service.validate_audio_format(file_content):
            logger.warning(f"오디오 형식 검증 실패: {file.filename}")
            # WebM이 아닌 경우에도 처리 시도 (다른 형식도 지원)
        
        # STT 처리 실행
        stt_result = stt_service.transcribe_audio_with_diarization(file_content)
        
        # 4. 새 conversation 생성
        conversation = Conversation(
            title=f"음성 대화 - {file.filename}",
            content=stt_result["transcript"][:1000],  # 처음 1000자만 저장
            family_id=family_id,
            create_date=datetime.now()
        )
        
        db.add(conversation)
        db.flush()  # ID 생성을 위해 flush
        
        # 5. 사용자를 conversation 참여자로 추가
        conversation.participants.append(current_user)
        
        # 6. 파일 서비스를 통해 GCS 업로드
        file_service = ConversationFileService(db)
        
        # 임시로 파일 객체 재생성 (file.read() 후 포인터 리셋)
        import io
        temp_file = UploadFile(
            filename=file.filename,
            file=io.BytesIO(file_content),
            headers=file.headers
        )
        
        # GCS 업로드
        gcs_path = file_service.file_processor.upload_to_gcs(
            file_content, current_user.id, file.filename
        )
        
        # 7. ConversationFile 레코드 생성 (음성 필드 포함)
        db_file = ConversationFile(
            conv_id=conversation.conv_id,
            gcs_file_path=gcs_path,
            original_filename=file.filename,
            file_type=file_extension,
            file_size=len(file_content),
            processing_status="completed",
            raw_content=stt_result["transcript"],
            # 음성 관련 필드
            audio_url=gcs_path,  # 음성 파일과 같은 경로
            transcript=stt_result["transcript"],
            speaker_segments=stt_result["speaker_segments"],
            duration=stt_result["duration"],
            speaker_count=stt_result["speaker_count"]
        )
        
        db.add(db_file)
        db.commit()
        
        logger.info(f"음성 파일 업로드 및 STT 처리 완료 - Conversation ID: {conversation.conv_id}")
        
        return FileUploadResponse(
            conversation_id=str(conversation.conv_id),
            file_id=db_file.id,
            status="completed",
            message="음성 파일이 성공적으로 업로드되고 텍스트로 변환되었습니다.",
            gcs_file_path=gcs_path
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"음성 파일 업로드 실패 (서버): {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@router.get("/audio/{conversation_id}")
async def get_audio_conversation_detail(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    음성 대화의 상세 정보를 조회합니다.
    
    Args:
        conversation_id: 대화 ID
        current_user: 현재 로그인한 사용자
        db: 데이터베이스 세션
        
    Returns:
        Dict: 음성 대화 상세 정보 (화자별 구간 포함)
    """
    logger.info(f"음성 대화 상세 조회 요청 - 사용자: {current_user.id}, 대화 ID: {conversation_id}")
    
    try:
        # 1. Conversation 존재 확인
        conversation = db.query(Conversation).filter(Conversation.conv_id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
        
        # 2. 사용자 권한 확인 (참여자인지 확인)
        if current_user not in conversation.participants:
            raise HTTPException(status_code=403, detail="해당 대화에 접근할 권한이 없습니다.")
        
        # 3. 음성 파일 정보 조회
        audio_file = (
            db.query(ConversationFile)
            .filter(ConversationFile.conv_id == conversation_id)
            .filter(ConversationFile.audio_url.isnot(None))  # 음성 파일만 조회
            .first()
        )
        
        if not audio_file:
            raise HTTPException(status_code=404, detail="음성 대화 파일을 찾을 수 없습니다.")
        
        # 4. 상세 정보 반환
        return {
            "conversation_id": str(conversation.conv_id),
            "title": conversation.title,
            "created_at": conversation.create_date,
            "family_id": conversation.family_id,
            "file_info": {
                "id": audio_file.id,
                "filename": audio_file.original_filename,
                "file_size": audio_file.file_size,
                "duration": audio_file.duration,
                "speaker_count": audio_file.speaker_count,
                "audio_url": audio_file.audio_url,
                "processing_status": audio_file.processing_status
            },
            "transcript": {
                "full_text": audio_file.transcript,
                "speaker_segments": audio_file.speaker_segments
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"음성 대화 상세 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"서버 오류가 발생했습니다: {str(e)}"
        )
