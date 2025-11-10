from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
import uuid

from .realtime_models import RealtimeSession, RealtimeMessage, SessionStatus, MessageType


class RealtimeService:
    def __init__(self, db: Session):
        self.db = db

    def create_free_session(self, room_name: str = "자유 대화방") -> RealtimeSession:
        """새로운 자유 대화 세션 생성 (가족 제약 없음)"""
        room_id = f"room_{uuid.uuid4().hex[:8]}"
        
        session = RealtimeSession(
            room_id=room_id,
            family_id=None,  # 가족 제약 없음
            status=SessionStatus.ACTIVE,
            display_name=room_name
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session

    def get_session_by_room_id(self, room_id: str) -> Optional[RealtimeSession]:
        """방 ID로 세션 조회"""
        return self.db.query(RealtimeSession).filter(
            RealtimeSession.room_id == room_id
        ).first()

    def get_all_active_sessions(self) -> List[RealtimeSession]:
        """모든 활성 세션 조회"""
        return self.db.query(RealtimeSession).filter(
            RealtimeSession.status == SessionStatus.ACTIVE
        ).order_by(RealtimeSession.created_at.desc()).all()

    def end_session(self, room_id: str) -> Optional[RealtimeSession]:
        """세션 종료"""
        session = self.get_session_by_room_id(room_id)
        if session and session.status == SessionStatus.ACTIVE:
            session.status = SessionStatus.ENDED
            session.ended_at = datetime.now()
            self.db.commit()
            self.db.refresh(session)
        
        return session

    def save_message(self, session_id: int, user_id: int, message: str, message_type: MessageType = MessageType.TEXT) -> RealtimeMessage:
        """메시지 저장"""
        db_message = RealtimeMessage(
            session_id=session_id,
            user_id=user_id,
            message=message,
            message_type=message_type
        )
        
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        
        return db_message

    def get_session_messages(self, session_id: int) -> List[RealtimeMessage]:
        """세션의 모든 메시지 조회"""
        return self.db.query(RealtimeMessage).filter(
            RealtimeMessage.session_id == session_id
        ).order_by(RealtimeMessage.timestamp).all()

    def export_conversation_as_text(self, session_id: int) -> str:
        """대화 내용을 텍스트로 변환"""
        messages = self.get_session_messages(session_id)
        
        if not messages:
            return ""
        
        text_lines = []
        for msg in messages:
            if msg.message_type == MessageType.TEXT:
                timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                text_lines.append(f"[{timestamp}] 사용자{msg.user_id}: {msg.message}")
        
        return "\n".join(text_lines)

    # 기존 가족 기반 메서드들 (호환성 유지)
    def create_session(self, family_id: int = None, room_name: str = "대화방") -> RealtimeSession:
        """기존 호환성을 위한 세션 생성"""
        return self.create_free_session(room_name)

    def get_active_sessions_by_family(self, family_id: int) -> List[RealtimeSession]:
        """가족별 활성 세션 조회 (빈 리스트 반환)"""
        return []
