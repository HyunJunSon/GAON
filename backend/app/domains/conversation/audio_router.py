from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form, BackgroundTasks
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


def convert_speaker_to_number(speaker_id):
    """SPEAKER_0A → 1001, SPEAKER_0B → 1002 형태로 변환 (실제 사용자 ID와 충돌 방지)"""
    if isinstance(speaker_id, str) and speaker_id.startswith('SPEAKER_'):
        # SPEAKER_0A → 1001, SPEAKER_0B → 1002 (1000번대 사용)
        suffix = speaker_id.split('_')[-1]  # 0A, 0B, 1A, 1B
        if len(suffix) >= 2:
            try:
                num = int(suffix[:-1])  # 0, 1, 2...
                letter = suffix[-1]     # A, B, C...
                # A=1, B=2, C=3... + 1000 (게스트 범위)
                letter_num = ord(letter) - ord('A') + 1
                return 1000 + num * 10 + letter_num
            except:
                pass
    return speaker_id


def format_transcript_for_agent(stt_result: dict, user_mapping: dict = None) -> str:
    """STT 결과를 Agent가 기대하는 형식으로 변환 (user_mapping 지원)"""
    speaker_segments = stt_result.get("speaker_segments", [])
    
    if not speaker_segments:
        # 화자 분리가 안된 경우 기본 형식
        transcript = stt_result.get("transcript", "")
        return f"참석자 1 00:00\n{transcript}"
    
    # 화자별 세그먼트를 Agent 형식으로 변환
    formatted_lines = []
    
    for segment in speaker_segments:
        speaker = segment.get("speaker", 1)
        start_time = segment.get("start", 0)
        text = segment.get("text", "")
        
        # user_mapping이 있으면 speaker 번호를 user_id로 치환
        if user_mapping and str(speaker) in user_mapping:
            mapped_user_id = user_mapping[str(speaker)]
            if mapped_user_id is not None:
                speaker = mapped_user_id
        else:
            # user_mapping에 없으면 숫자 ID로 변환 (게스트 처리)
            speaker = convert_speaker_to_number(speaker)
        
        # 시간을 MM:SS 형식으로 변환
        minutes = int(start_time // 60)
        seconds = int(start_time % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"
        
        formatted_lines.append(f"참석자 {speaker} {timestamp}")
        formatted_lines.append(text)
        formatted_lines.append("")  # 빈 줄 추가
    
    return "\n".join(formatted_lines)


@router.post("/audio", response_model=FileUploadResponse)
async def upload_audio_conversation(
    background_tasks: BackgroundTasks,
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
        
        # STT 처리 실행 (WebM은 AssemblyAI 우선 사용)
        if file_extension == 'webm':
            logger.info("WebM 파일 - AssemblyAI 사용")
            try:
                stt_result = stt_service.assemblyai_client.transcribe_with_speakers(file_content, file.filename)
                # AssemblyAI 응답 형식을 Google STT 형식으로 변환
                if 'segments' in stt_result:
                    stt_result['speaker_segments'] = stt_result['segments']
                if 'full_text' in stt_result:
                    stt_result['transcript'] = stt_result['full_text']
                # 기본값 설정
                stt_result.setdefault('transcript', '')
                stt_result.setdefault('speaker_segments', [])
                stt_result.setdefault('duration', 0)
                stt_result.setdefault('speaker_count', 0)
            except Exception as e:
                logger.warning(f"AssemblyAI 실패, Google STT로 대체: {str(e)}")
                stt_result = stt_service.transcribe_audio_with_diarization(file_content, file.filename)
        else:
            # 다른 형식은 Google STT 사용
            stt_result = stt_service.transcribe_audio_with_diarization(file_content, file.filename)
        
        # STT 실패 시에도 파일은 저장하되 상태 표시
        processing_status = "completed" if stt_result["transcript"] else "stt_failed"
        transcript_text = stt_result["transcript"] or "음성 인식 처리 실패"
        
        # STT 결과를 Agent 기대 형식으로 변환
        formatted_content = format_transcript_for_agent(stt_result)
        
        # 4. 새 conversation 생성
        conversation = Conversation(
            title=f"음성 대화 - {file.filename}",
            content=formatted_content[:1000],  # Agent 형식으로 저장
            id=current_user.id,  # 사용자 ID 저장
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
    logger.info(f"요청된 화자 매핑: {request.speaker_mapping}")
    
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
        
        # 4. 화자 매핑 유효성 검사 (임시로 완화)
        # if audio_file.speaker_count:
        #     valid_speakers = {str(i) for i in range(audio_file.speaker_count)}
        #     invalid_speakers = set(request.speaker_mapping.keys()) - valid_speakers
        #     
        #     if invalid_speakers:
        #         raise HTTPException(
        #             status_code=400, 
        #             detail=f"유효하지 않은 화자 ID: {invalid_speakers}. 유효한 화자: {valid_speakers}"
        #         )
        
        # 5. 화자 매핑 업데이트 (사용자 ID 정보 포함)
        mapping_data = {
            "speaker_names": request.speaker_mapping,
            "user_ids": request.user_mapping or {}
        }
        audio_file.speaker_mapping = mapping_data
        
        # 6. user_mapping이 있으면 conversation content도 업데이트
        if request.user_mapping:
            # STT 결과에서 user_mapping 적용한 새로운 content 생성
            stt_result = {
                "speaker_segments": audio_file.speaker_segments or [],
                "transcript": audio_file.transcript or ""
            }
            updated_content = format_transcript_for_agent(stt_result, request.user_mapping)
            conversation.content = updated_content
            logger.info(f"Conversation content 업데이트됨 - user_mapping 적용")
        
        db.commit()
        
        logger.info(f"화자 매핑 설정 완료 - 대화 ID: {conversation_id}, 매핑: {request.speaker_mapping}, 사용자 매핑: {request.user_mapping}")
        
        # 7. 매핑 완료 후 자동으로 분석 파이프라인 시작
        try:
            from app.domains.conversation.router import run_agent_pipeline_async
            
            # 백그라운드에서 분석 파이프라인 실행
            background_tasks.add_task(run_agent_pipeline_async, str(conversation_id), current_user.id)
            logger.info(f"분석 파이프라인 자동 시작됨 - 대화 ID: {conversation_id}")
        except Exception as e:
            logger.warning(f"분석 파이프라인 자동 시작 실패: {str(e)}")
        
        return SpeakerMappingResponse(
            conversation_id=str(conversation_id),
            file_id=audio_file.id,
            speaker_mapping=request.speaker_mapping,
            user_mapping=request.user_mapping,
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
        
        # 4. 매핑된 세그먼트 생성 (하위 호환성 처리)
        mapped_segments = []
        speaker_mapping = audio_file.speaker_mapping or {}
        
        # 새로운 형식 (speaker_names, user_ids) 또는 기존 형식 처리
        if isinstance(speaker_mapping, dict):
            if "speaker_names" in speaker_mapping:
                # 새로운 형식
                speaker_names = speaker_mapping.get("speaker_names", {})
                user_ids = speaker_mapping.get("user_ids", {})
            else:
                # 기존 형식 (하위 호환성)
                speaker_names = speaker_mapping
                user_ids = {}
        else:
            speaker_names = {}
            user_ids = {}
        
        if audio_file.speaker_segments:
            for segment in audio_file.speaker_segments:
                speaker_id = str(segment.get("speaker", ""))
                speaker_name = speaker_names.get(speaker_id, speaker_id)
                
                start_time = segment.get("start", 0)
                end_time = segment.get("end", 0)
                
                # 시:분:초 형태로 변환
                def format_time(seconds):
                    minutes = int(seconds // 60)
                    secs = int(seconds % 60)
                    return f"{minutes:02d}:{secs:02d}"
                
                mapped_segments.append({
                    "speaker": segment.get("speaker"),
                    "speaker_name": speaker_name,
                    "start": start_time,
                    "end": end_time,
                    "start_time": format_time(start_time),
                    "end_time": format_time(end_time),
                    "duration": round(end_time - start_time, 2),
                    "text": segment.get("text")
                })
        
        return {
            "conversation_id": str(conversation_id),
            "file_id": audio_file.id,
            "speaker_mapping": speaker_names,
            "user_mapping": user_ids,
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
