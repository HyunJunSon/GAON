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
from .speaker_schemas import SpeakerMappingRequest, SpeakerMappingResponse, SpeakerSplitRequest

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
        if not stt_service.validate_audio_format(file_content, file.filename):
            logger.warning(f"오디오 형식 검증 실패: {file.filename}")
            # 검증 실패해도 처리 시도 (일부 파일은 시그니처가 다를 수 있음)
        
        # STT 처리 실행 (파일명 전달)
        stt_result = stt_service.transcribe_audio_with_diarization(file_content, file.filename)
        
        # STT 실패 시에도 파일은 저장하되 상태 표시
        processing_status = "completed" if stt_result["transcript"] else "stt_failed"
        transcript_text = stt_result["transcript"] or "음성 인식 처리 실패"
        
        # 4. 새 conversation 생성
        conversation = Conversation(
            title=f"음성 대화 - {file.filename}",
            content=transcript_text[:1000],  # 처음 1000자만 저장
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
            processing_status=processing_status,
            raw_content=transcript_text,
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


@router.put("/audio/{conversation_id}/speaker-mapping", response_model=SpeakerMappingResponse)
async def update_speaker_mapping(
    conversation_id: UUID,
    request: SpeakerMappingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    음성 대화의 화자 매핑을 설정합니다.
    
    Args:
        conversation_id: 대화 ID
        request: 화자 매핑 정보
        current_user: 현재 로그인한 사용자
        db: 데이터베이스 세션
        
    Returns:
        SpeakerMappingResponse: 매핑 설정 결과
    """
    logger.info(f"화자 매핑 설정 요청 - 사용자: {current_user.id}, 대화 ID: {conversation_id}")
    
    try:
        # 1. Conversation 존재 확인
        conversation = db.query(Conversation).filter(Conversation.conv_id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
        
        # 2. 사용자 권한 확인
        if current_user not in conversation.participants:
            raise HTTPException(status_code=403, detail="해당 대화에 접근할 권한이 없습니다.")
        
        # 3. 음성 파일 정보 조회
        audio_file = (
            db.query(ConversationFile)
            .filter(ConversationFile.conv_id == conversation_id)
            .filter(ConversationFile.audio_url.isnot(None))
            .first()
        )
        
        if not audio_file:
            raise HTTPException(status_code=404, detail="음성 대화 파일을 찾을 수 없습니다.")
        
        # 4. 화자 매핑 유효성 검사
        if audio_file.speaker_count:
            valid_speakers = {str(i) for i in range(audio_file.speaker_count)}
            invalid_speakers = set(request.speaker_mapping.keys()) - valid_speakers
            
            if invalid_speakers:
                raise HTTPException(
                    status_code=400, 
                    detail=f"유효하지 않은 화자 ID: {invalid_speakers}. 유효한 화자: {valid_speakers}"
                )
        
        # 5. 화자 매핑 업데이트
        audio_file.speaker_mapping = request.speaker_mapping
        db.commit()
        
        logger.info(f"화자 매핑 설정 완료 - 대화 ID: {conversation_id}, 매핑: {request.speaker_mapping}")
        
        return SpeakerMappingResponse(
            conversation_id=str(conversation_id),
            file_id=audio_file.id,
            speaker_mapping=request.speaker_mapping,
            message="화자 매핑이 성공적으로 설정되었습니다."
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"화자 매핑 설정 실패: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@router.get("/audio/{conversation_id}/speaker-mapping")
async def get_speaker_mapping(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    음성 대화의 화자 매핑 정보를 조회합니다.
    
    Args:
        conversation_id: 대화 ID
        current_user: 현재 로그인한 사용자
        db: 데이터베이스 세션
        
    Returns:
        Dict: 화자 매핑 정보와 매핑된 세그먼트
    """
    logger.info(f"화자 매핑 조회 요청 - 사용자: {current_user.id}, 대화 ID: {conversation_id}")
    
    try:
        # 1. Conversation 존재 확인
        conversation = db.query(Conversation).filter(Conversation.conv_id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
        
        # 2. 사용자 권한 확인
        if current_user not in conversation.participants:
            raise HTTPException(status_code=403, detail="해당 대화에 접근할 권한이 없습니다.")
        
        # 3. 음성 파일 정보 조회
        audio_file = (
            db.query(ConversationFile)
            .filter(ConversationFile.conv_id == conversation_id)
            .filter(ConversationFile.audio_url.isnot(None))
            .first()
        )
        
        if not audio_file:
            raise HTTPException(status_code=404, detail="음성 대화 파일을 찾을 수 없습니다.")
        
        # 4. 매핑된 세그먼트 생성
        mapped_segments = []
        speaker_mapping = audio_file.speaker_mapping or {}
        
        if audio_file.speaker_segments:
            for segment in audio_file.speaker_segments:
                speaker_id = str(segment.get("speaker", ""))
                mapped_segments.append({
                    "speaker": segment.get("speaker"),
                    "speaker_name": speaker_mapping.get(speaker_id),
                    "start": segment.get("start"),
                    "end": segment.get("end"),
                    "text": segment.get("text")
                })
        
        return {
            "conversation_id": str(conversation_id),
            "file_id": audio_file.id,
            "speaker_mapping": speaker_mapping,
            "speaker_count": audio_file.speaker_count,
            "mapped_segments": mapped_segments
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"화자 매핑 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@router.post("/audio/{conversation_id}/improve-speaker-separation")
async def improve_speaker_separation(
    conversation_id: UUID,
    request: SpeakerSplitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    화자 분리를 개선합니다 (시간 기반 또는 수동 할당).
    
    Args:
        conversation_id: 대화 ID
        request: 화자 분리 개선 요청
        current_user: 현재 로그인한 사용자
        db: 데이터베이스 세션
        
    Returns:
        Dict: 개선된 화자 분리 결과
    """
    logger.info(f"화자 분리 개선 요청 - 사용자: {current_user.id}, 대화 ID: {conversation_id}")
    
    try:
        # 1. 권한 확인
        conversation = db.query(Conversation).filter(Conversation.conv_id == conversation_id).first()
        if not conversation or current_user not in conversation.participants:
            raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
        
        # 2. 음성 파일 조회
        audio_file = (
            db.query(ConversationFile)
            .filter(ConversationFile.conv_id == conversation_id)
            .filter(ConversationFile.audio_url.isnot(None))
            .first()
        )
        
        if not audio_file or not audio_file.speaker_segments:
            raise HTTPException(status_code=404, detail="음성 대화 데이터를 찾을 수 없습니다.")
        
        # 3. 화자 분리 개선 적용
        original_segments = audio_file.speaker_segments
        
        if request.split_method == "time_based":
            improved_segments = _improve_by_time_interval(original_segments, request.split_interval)
        elif request.split_method == "manual" and request.manual_assignments:
            improved_segments = _apply_manual_assignments(original_segments, request.manual_assignments)
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 분리 방법입니다.")
        
        # 4. 결과 저장
        audio_file.speaker_segments = improved_segments
        
        # 화자 수 재계산
        speakers = set(seg['speaker'] for seg in improved_segments)
        audio_file.speaker_count = len(speakers)
        
        db.commit()
        
        logger.info(f"화자 분리 개선 완료 - 대화 ID: {conversation_id}, 방법: {request.split_method}")
        
        return {
            "conversation_id": str(conversation_id),
            "method": request.split_method,
            "original_segments": len(original_segments),
            "improved_segments": len(improved_segments),
            "speaker_count": audio_file.speaker_count,
            "message": "화자 분리가 개선되었습니다."
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"화자 분리 개선 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")


def _improve_by_time_interval(segments: list, interval: float) -> list:
    """시간 간격 기반으로 화자 분리 개선"""
    if not segments:
        return segments
    
    improved_segments = []
    current_speaker = 0
    
    for segment in segments:
        # 시간 간격에 따라 화자 교대
        time_slot = int(segment['start'] // interval)
        new_speaker = time_slot % 2  # 0과 1 사이에서 교대
        
        new_segment = segment.copy()
        new_segment['speaker'] = new_speaker
        improved_segments.append(new_segment)
    
    return improved_segments


def _apply_manual_assignments(segments: list, assignments: list) -> list:
    """수동 할당 적용"""
    improved_segments = segments.copy()
    
    for assignment in assignments:
        segment_index = assignment.get('segment_index')
        new_speaker = assignment.get('speaker')
        
        if 0 <= segment_index < len(improved_segments):
            improved_segments[segment_index]['speaker'] = new_speaker
    
    return improved_segments
