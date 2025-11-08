from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
import uuid

from .realtime_models import RealtimeSession, RealtimeMessage, SessionStatus, MessageType
from .realtime_schemas import SessionCreate, MessageCreate, SessionResponse, MessageResponse


class RealtimeService:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, family_id: int, room_name: str = "가족 대화방") -> RealtimeSession:
        """새로운 실시간 대화 세션 생성 또는 기존 활성 세션 반환"""
        # 같은 가족의 활성 세션이 있는지 확인
        existing_session = self.db.query(RealtimeSession).filter(
            and_(
                RealtimeSession.family_id == family_id,
                RealtimeSession.status == SessionStatus.ACTIVE
            )
        ).first()
        
        if existing_session:
            return existing_session
        
        # 활성 세션이 없으면 새로 생성
        room_id = f"room_{uuid.uuid4().hex[:8]}"
        
        session = RealtimeSession(
            room_id=room_id,
            family_id=family_id,
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

    def get_active_sessions_by_family(self, family_id: int) -> List[RealtimeSession]:
        """가족의 활성 세션 목록 조회"""
        return self.db.query(RealtimeSession).filter(
            and_(
                RealtimeSession.family_id == family_id,
                RealtimeSession.status == SessionStatus.ACTIVE
            )
        ).all()

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
