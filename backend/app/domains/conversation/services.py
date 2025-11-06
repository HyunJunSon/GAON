from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException
from datetime import datetime
from typing import List
from .file_models import ConversationFile
from .models import Conversation
from .file_processor import FileProcessor
from .schemas import ALLOWED_FILE_TYPES, MAX_FILE_SIZE


class ConversationFileService:
    def __init__(self, db: Session):
        self.db = db
        self.file_processor = FileProcessor()

    async def upload_file_and_create_conversation(self, user_id: int, family_id: int, file: UploadFile) -> tuple[Conversation, ConversationFile]:
        """파일 업로드 및 새 conversation 생성"""
        
        # 1. 기본 유효성 검사
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(ALLOWED_FILE_TYPES)}"
            )

        # 2. 파일 내용 읽기
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"파일 크기가 너무 큽니다. 최대 크기: {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # 3. 파일 내용 유효성 검사
        if not self.file_processor.validate_file_content(file_content, file_extension):
            raise HTTPException(status_code=400, detail="파일이 손상되었거나 유효하지 않습니다.")

        try:
            # 4. 새 conversation 생성
            conversation = Conversation(
                title=f"대화 분석 - {file.filename}",
                content="",  # 파일 처리 후 업데이트
                user_id=user_id,
                family_id=family_id,
                create_date=datetime.now()
            )
            
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
            
            # 5. GCS에 업로드
            gcs_path = self.file_processor.upload_to_gcs(file_content, user_id, file.filename)
            
            # 6. 텍스트 추출
            raw_content = self.file_processor.extract_text(file_content, file_extension)
            
            # 7. 파일 정보 DB에 저장
            db_file = ConversationFile(
                conversation_id=conversation.id,
                gcs_file_path=gcs_path,
                original_filename=file.filename,
                file_type=file_extension,
                file_size=file_size,
                processing_status="processing",
                raw_content=raw_content
            )
            
            self.db.add(db_file)
            
            # 8. conversation content 업데이트
            conversation.content = raw_content[:1000]  # 처음 1000자만 저장
            
            # 9. 처리 완료
            db_file.processing_status = "completed"
            db_file.processed_date = datetime.now()
            
            self.db.commit()
            self.db.refresh(db_file)
            
            return conversation, db_file
            
        except Exception as e:
            self.db.rollback()
            # 실패 시 GCS에서 파일 삭제
            if 'gcs_path' in locals():
                self.file_processor.delete_from_gcs(gcs_path)
            raise HTTPException(status_code=500, detail=f"파일 처리 중 오류가 발생했습니다: {str(e)}")
        """파일 업로드 및 처리"""
        
        # 1. 기본 유효성 검사
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(ALLOWED_FILE_TYPES)}"
            )

        # 2. 파일 내용 읽기
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"파일 크기가 너무 큽니다. 최대 크기: {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        # 3. 파일 내용 유효성 검사
        if not self.file_processor.validate_file_content(file_content, file_extension):
            raise HTTPException(status_code=400, detail="파일이 손상되었거나 유효하지 않습니다.")

        try:
            # 4. GCS에 업로드
            gcs_path = self.file_processor.upload_to_gcs(file_content, user_id, file.filename)
            
            # 5. 텍스트 추출
            raw_content = self.file_processor.extract_text(file_content, file_extension)
            
            # 6. DB에 저장
            db_file = ConversationFile(
                conversation_id=conversation_id,
                gcs_file_path=gcs_path,
                original_filename=file.filename,
                file_type=file_extension,
                file_size=file_size,
                processing_status="processing",
                raw_content=raw_content
            )
            
            self.db.add(db_file)
            self.db.commit()
            self.db.refresh(db_file)
            
            # 7. 처리 완료 상태 업데이트
            db_file.processing_status = "completed"
            db_file.processed_date = datetime.now()
            self.db.commit()
            
            return db_file
            
        except Exception as e:
            # 실패 시 GCS에서 파일 삭제
            if 'gcs_path' in locals():
                self.file_processor.delete_from_gcs(gcs_path)
            raise HTTPException(status_code=500, detail=f"파일 처리 중 오류가 발생했습니다: {str(e)}")

    def get_file_by_id(self, file_id: int) -> ConversationFile:
        """파일 ID로 조회"""
        db_file = self.db.query(ConversationFile).filter(ConversationFile.id == file_id).first()
        if not db_file:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
        return db_file

    def get_files_by_user_id(self, user_id: int) -> List[ConversationFile]:
        """사용자 ID로 업로드한 모든 파일 조회"""
        files = (
            self.db.query(ConversationFile)
            .join(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(ConversationFile.upload_date.desc())
            .all()
        )
        return files

    def get_conversation_analysis(self, conversation_id: int) -> dict:
        """대화 분석 결과 조회 (현재는 기본값 반환)"""
        # conversation 존재 확인
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
        
        # TODO: 실제 LLM 분석 로직으로 교체 예정
        return {
            "summary": "이 대화는 가족 간의 일상적인 소통을 담고 있습니다. 전반적으로 긍정적인 분위기이며, 서로에 대한 관심과 배려가 잘 드러나고 있습니다.",
            "emotion": {
                "overall_sentiment": "positive",
                "emotion_scores": {
                    "joy": 0.7,
                    "sadness": 0.1,
                    "anger": 0.05,
                    "fear": 0.05,
                    "surprise": 0.1
                },
                "temperature": 75  # 감정 온도
            },
            "dialog": [
                {
                    "speaker": "사용자1",
                    "message": "오늘 하루 어땠어?",
                    "emotion": "neutral",
                    "timestamp": "2024-01-01 09:00:00"
                },
                {
                    "speaker": "사용자2", 
                    "message": "좋았어! 새로운 프로젝트 시작했거든",
                    "emotion": "joy",
                    "timestamp": "2024-01-01 09:01:00"
                }
            ],
            "status": "completed",
            "updated_at": datetime.now()
        }
