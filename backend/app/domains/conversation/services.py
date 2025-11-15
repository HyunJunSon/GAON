from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import UploadFile, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .models import Conversation
from .file_models import ConversationFile
from .file_processor import FileProcessor
from app.domains.auth.user_models import User
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConversationFileService:
    def __init__(self, db: Session):
        self.db = db
        self.file_processor = FileProcessor()

    async def upload_file_and_create_conversation(self, user_id: int, family_id: int, file: UploadFile) -> tuple[Conversation, ConversationFile]:
        """파일 업로드 및 새 conversation 생성"""
        
        file_extension = self._validate_file(file)
        
        # 파일 내용 읽기
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=400, 
                detail=f"파일 크기가 너무 큽니다. 최대 크기: {settings.max_file_size // (1024*1024)}MB"
            )

        # 파일 내용 유효성 검사
        if not self.file_processor.validate_file_content(file_content, file_extension):
            raise HTTPException(status_code=400, detail="파일이 손상되었거나 유효하지 않습니다.")

        try:
            # 사용자 존재 확인
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
            
            # 새 conversation 생성
            conversation = Conversation(
                title=f"대화 분석 - {file.filename}",
                content="",  # 파일 처리 후 업데이트
                family_id=family_id,
                create_date=datetime.now()
            )
            
            self.db.add(conversation)
            self.db.flush()  # ID 생성을 위해 flush
            
            # Many-to-Many 관계 설정 (사용자를 conversation 참여자로 추가)
            conversation.participants.append(user)
            
            # GCS에 업로드
            gcs_path = self.file_processor.upload_to_gcs(file_content, user_id, file.filename)
            
            # 텍스트 추출
            raw_content = self.file_processor.extract_text(file_content, file_extension)
            
            # 파일 정보 DB에 저장
            db_file = ConversationFile(
                conv_id=conversation.conv_id,
                gcs_file_path=gcs_path,
                original_filename=file.filename,
                file_type=file_extension,
                file_size=file_size,
                processing_status="completed",
                raw_content=raw_content,
                processed_date=datetime.now()
            )
            
            self.db.add(db_file)
            
            # conversation content 업데이트
            conversation.content = raw_content[:1000]  # 처음 1000자만 저장
            
            self.db.commit()
            
            logger.info(f"파일 업로드 완료: {file.filename}, Conversation ID: {conversation.id}")
            return conversation, db_file
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"파일 업로드 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=500, detail=f"파일 처리 중 오류가 발생했습니다: {str(e)}")
    def _validate_file(self, file: UploadFile) -> str:
        """파일 유효성 검사 공통 로직"""
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(settings.allowed_file_types)}"
            )
        
        return file_extension

    async def upload_file_to_conversation(self, conv_id: str, user_id: int, file: UploadFile) -> ConversationFile:
        """기존 conversation에 파일 업로드"""
        file_extension = self._validate_file(file)
        
        # 파일 내용 읽기
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=400, 
                detail=f"파일 크기가 너무 큽니다. 최대 크기: {settings.max_file_size // (1024*1024)}MB"
            )

        # 파일 내용 유효성 검사
        if not self.file_processor.validate_file_content(file_content, file_extension):
            raise HTTPException(status_code=400, detail="파일이 손상되었거나 유효하지 않습니다.")

        try:
            # Conversation 존재 확인
            conversation = self.db.query(Conversation).filter(Conversation.conv_id == conv_id).first()
            if not conversation:
                raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
            
            # 사용자가 해당 conversation의 참여자인지 확인
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or user not in conversation.participants:
                raise HTTPException(status_code=403, detail="해당 대화에 참여할 권한이 없습니다.")
            
            # GCS에 업로드
            gcs_path = self.file_processor.upload_to_gcs(file_content, user_id, file.filename)
            
            # 텍스트 추출
            raw_content = self.file_processor.extract_text(file_content, file_extension)
            
            # DB에 저장
            db_file = ConversationFile(
                conv_id=conv_id,
                gcs_file_path=gcs_path,
                original_filename=file.filename,
                file_type=file_extension,
                file_size=file_size,
                processing_status="completed",
                raw_content=raw_content,
                processed_date=datetime.now()
            )
            
            self.db.add(db_file)
            self.db.commit()
            self.db.refresh(db_file)
            
            logger.info(f"파일 추가 완료: {file.filename}, Conversation ID: {conv_id}")
            return db_file
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"파일 업로드 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=500, detail=f"파일 처리 중 오류가 발생했습니다: {str(e)}")

    def get_file_by_id(self, file_id: int) -> ConversationFile:
        """파일 ID로 파일 정보 조회"""
        db_file = self.db.query(ConversationFile).filter(ConversationFile.id == file_id).first()
        if not db_file:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        return db_file

    def get_files_by_user_id(self, user_id: int) -> List[ConversationFile]:
        """사용자 ID로 업로드한 모든 파일 조회"""
        files = (
            self.db.query(ConversationFile)
            .join(Conversation)
            .join(Conversation.participants)
            .filter(User.id == user_id)
            .order_by(ConversationFile.upload_date.desc())
            .all()
        )
        return files

    def get_conversation_analysis(self, conv_id: str) -> Dict[str, Any]:
        """대화 분석 결과 조회"""
        conversation = self.db.query(Conversation).filter(Conversation.conv_id == conv_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
        
        # 파일들의 분석 결과 통합
        files = self.db.query(ConversationFile).filter(ConversationFile.conv_id == conv_id).all()
        
        # 임시 분석 결과 (실제로는 LLM 분석 결과를 반환)
        return {
            "summary": conversation.content[:500] + "..." if len(conversation.content) > 500 else conversation.content,
            "emotion": {"positive": 0.7, "negative": 0.2, "neutral": 0.1},
            "dialog": [{"speaker": "User", "content": "분석된 대화 내용"}],
            "status": "completed",
            "updated_at": conversation.create_date
        }

    def get_conversation_by_id(self, conv_id: str) -> Optional[Dict[str, Any]]:
        """대화 ID로 대화 조회"""
        conversation = self.db.query(Conversation).filter(Conversation.conv_id == conv_id).first()
        if not conversation:
            return None
        
        return {
            "conv_id": str(conversation.conv_id),
            "title": conversation.title,
            "content": conversation.content,
            "family_id": conversation.family_id,
            "create_date": conversation.create_date
        }
