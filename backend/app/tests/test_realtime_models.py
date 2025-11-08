import pytest
from app.domains.conversation.realtime_models import RealtimeSession, RealtimeMessage, SessionStatus, MessageType


def test_realtime_session_creation():
    """RealtimeSession 모델 생성 테스트"""
    session = RealtimeSession(
        room_id="test_room_123",
        family_id=1,
        status=SessionStatus.ACTIVE
    )
    
    assert session.room_id == "test_room_123"
    assert session.family_id == 1
    assert session.status == SessionStatus.ACTIVE
    assert session.ended_at is None


def test_realtime_message_creation():
    """RealtimeMessage 모델 생성 테스트"""
    message = RealtimeMessage(
        session_id=1,
        user_id=1,
        message="안녕하세요!",
        message_type=MessageType.TEXT
    )
    
    assert message.session_id == 1
    assert message.user_id == 1
    assert message.message == "안녕하세요!"
    assert message.message_type == MessageType.TEXT


def test_session_status_enum():
    """SessionStatus enum 테스트"""
    assert SessionStatus.ACTIVE.value == "active"
    assert SessionStatus.ENDED.value == "ended"


def test_message_type_enum():
    """MessageType enum 테스트"""
    assert MessageType.TEXT.value == "text"
    assert MessageType.SYSTEM.value == "system"
