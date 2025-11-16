from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging
import asyncio

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.auth.auth_schema import User
from .services import ConversationFileService
from .schemas import ConversationFileResponse, FileUploadResponse, ConversationAnalysisResponse

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["conversations"])


@router.post("/conversations/analyze", response_model=FileUploadResponse)
async def upload_conversation_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    family_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """대화 파일 업로드 및 분석 - 새 conversation 생성"""
    logger.info(f"파일 업로드 요청: user_id={current_user.id}, filename={file.filename}")
    
    service = ConversationFileService(db)
    
    # family_id가 없으면 기본값 1 사용 (추후 사용자별 family 관리 구현 예정)
    if family_id is None:
        family_id = 1
        logger.debug(f"family_id 기본값 사용: {family_id}")
    
    try:
        conversation, db_file = await service.upload_file_and_create_conversation(
            current_user.id, family_id, file
        )
        
        # 🚀 자동 분석 시작 추가
        background_tasks.add_task(
            run_agent_pipeline_async, 
            str(conversation.conv_id), 
            current_user.id
        )
        
        logger.info(f"파일 업로드 성공 및 분석 시작: conversation_id={conversation.conv_id}, file_id={db_file.id}")
        
        return FileUploadResponse(
            message="파일이 성공적으로 업로드되고 분석이 시작되었습니다.",
            conversation_id=str(conversation.conv_id),
            file_id=db_file.id,
            status=db_file.processing_status,
            gcs_file_path=db_file.gcs_file_path
        )
    except HTTPException as e:
        logger.warning(f"파일 업로드 실패 (HTTP): user_id={current_user.id}, error={e.detail}")
        raise
    except Exception as e:
        logger.error(f"파일 업로드 실패 (서버): user_id={current_user.id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


@router.get("/analysis/{conversation_id}", response_model=ConversationAnalysisResponse)
def get_conversation_analysis(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """대화 분석 결과 조회"""
    logger.info(f"분석 결과 조회: user_id={current_user.id}, conversation_id={conversation_id}")
    
    service = ConversationFileService(db)
    
    try:
        analysis_data = service.get_conversation_analysis(str(conversation_id))
        logger.info(f"분석 결과 조회 성공: conversation_id={conversation_id}")
        return ConversationAnalysisResponse(**analysis_data)
    except HTTPException as e:
        logger.warning(f"분석 결과 조회 실패 (HTTP): conversation_id={conversation_id}, error={e.detail}")
        raise
    except Exception as e:
        logger.error(f"분석 결과 조회 실패 (서버): conversation_id={conversation_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


@router.get("/conversations/files/{file_id}", response_model=ConversationFileResponse)
def get_conversation_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """파일 정보 조회"""
    logger.info(f"파일 정보 조회: user_id={current_user.id}, file_id={file_id}")
    
    service = ConversationFileService(db)
    try:
        file_info = service.get_file_by_id(file_id)
        logger.info(f"파일 정보 조회 성공: file_id={file_id}")
        return file_info
    except HTTPException as e:
        logger.warning(f"파일 정보 조회 실패: file_id={file_id}, error={e.detail}")
        raise
    except Exception as e:
        logger.error(f"파일 정보 조회 실패 (서버): file_id={file_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


@router.get("/conversations/files", response_model=List[ConversationFileResponse])
def get_user_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """현재 사용자가 업로드한 모든 파일 조회"""
    logger.info(f"사용자 파일 목록 조회: user_id={current_user.id}")
    
    service = ConversationFileService(db)
    try:
        files = service.get_files_by_user_id(current_user.id)
        logger.info(f"사용자 파일 목록 조회 성공: user_id={current_user.id}, count={len(files)}")
        return files
    except Exception as e:
        logger.error(f"사용자 파일 목록 조회 실패: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


@router.post("/analysis/{conversation_id}/start")
async def start_analysis_pipeline(
    conversation_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Agent 파이프라인 비동기 실행"""
    logger.info(f"분석 파이프라인 시작: user_id={current_user.id}, conversation_id={conversation_id}")
    
    service = ConversationFileService(db)
    
    try:
        # 대화 존재 확인
        conversation = service.get_conversation_by_id(str(conversation_id))
        if not conversation:
            raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
        
        # 백그라운드에서 Agent 파이프라인 실행
        background_tasks.add_task(
            run_agent_pipeline_async, 
            str(conversation_id), 
            current_user.id
        )
        
        logger.info(f"분석 파이프라인 시작됨: conversation_id={conversation_id}")
        
        return {
            "status": "started",
            "conversation_id": str(conversation_id),
            "message": "분석이 시작되었습니다."
        }
        
    except HTTPException as e:
        logger.warning(f"분석 시작 실패 (HTTP): conversation_id={conversation_id}, error={e.detail}")
        raise
    except Exception as e:
        logger.error(f"분석 시작 실패 (서버): conversation_id={conversation_id}, error={str(e)}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


async def run_agent_pipeline_async(conversation_id: str, user_id: int):
    """비동기 Agent 파이프라인 실행 (재시도 로직 포함)"""
    try:
        logger.info(f"재시도 가능한 Agent 파이프라인 실행 시작: conv_id={conversation_id}")
        
        # 재시도 로직이 포함된 파이프라인 실행
        from app.llm.agent.retry_pipeline import run_agent_pipeline_with_retry
        
        result = await run_agent_pipeline_with_retry(conversation_id)
        
        logger.info(f"Agent 파이프라인 완료: conv_id={conversation_id}, status={result.get('status')}")
        
        # 성공/실패에 따른 추가 처리 (알림 등)
        if result.get("status") == "completed":
            logger.info(f"분석 성공: score={result.get('score')}, confidence={result.get('confidence')}")
        else:
            logger.error(f"분석 실패: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Agent 파이프라인 실행 실패: conv_id={conversation_id}, error={str(e)}")
        return {"status": "failed", "error": str(e)}


def execute_agent_pipeline(conversation_id: str):
    """Agent 파이프라인 실행 (동기) - 레거시 호환용"""
    import asyncio
    
    # 환경 변수 설정
    import os
    os.environ["USE_TEST_DB"] = "false"
    
    # 비동기 파이프라인 실행
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            run_agent_pipeline_async(conversation_id, 0)
        )
    finally:
        loop.close()
