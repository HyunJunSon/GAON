import pytest
from unittest.mock import MagicMock
from app.domains.conversation.realtime_services import RealtimeService
from app.domains.conversation.realtime_models import RealtimeSession, RealtimeMessage, SessionStatus, MessageType


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return RealtimeService(mock_db)


def test_create_session(service, mock_db):
    """세션 생성 테스트"""
    family_id = 1
    
    # Mock 설정
    mock_session = RealtimeSession(id=1, room_id="room_12345678", family_id=family_id)
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    # 실제 객체 생성을 위해 service의 create_session을 부분적으로 모킹
    service.db = mock_db
    
    # 실행
    result = service.create_session(family_id)
    
    # 검증
    assert result.family_id == family_id
    assert result.status == SessionStatus.ACTIVE
    assert result.room_id.startswith("room_")
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_get_session_by_room_id(service, mock_db):
    """방 ID로 세션 조회 테스트"""
    room_id = "room_12345678"
    mock_session = RealtimeSession(id=1, room_id=room_id, family_id=1)
    
    # Mock 설정
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.first.return_value = mock_session
    
    # 실행
    result = service.get_session_by_room_id(room_id)
    
    # 검증
    assert result == mock_session
    mock_db.query.assert_called_once_with(RealtimeSession)


def test_save_message(service, mock_db):
    """메시지 저장 테스트"""
    session_id = 1
    user_id = 1
    message = "안녕하세요!"
    
    # Mock 설정
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    # 실행
    result = service.save_message(session_id, user_id, message)
    
    # 검증
    assert result.session_id == session_id
    assert result.user_id == user_id
    assert result.message == message
    assert result.message_type == MessageType.TEXT
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_end_session(service, mock_db):
    """세션 종료 테스트"""
    room_id = "room_12345678"
    mock_session = RealtimeSession(id=1, room_id=room_id, family_id=1, status=SessionStatus.ACTIVE)
    
    # Mock 설정
    service.get_session_by_room_id = MagicMock(return_value=mock_session)
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    # 실행
    result = service.end_session(room_id)
    
    # 검증
    assert result.status == SessionStatus.ENDED
    assert result.ended_at is not None
    mock_db.commit.assert_called_once()


def test_export_conversation_as_text(service, mock_db):
    """대화 텍스트 변환 테스트"""
    session_id = 1
    
    # Mock 메시지들
    from datetime import datetime
    mock_messages = [
        RealtimeMessage(
            id=1, session_id=session_id, user_id=1, 
            message="안녕하세요!", message_type=MessageType.TEXT,
            timestamp=datetime(2023, 1, 1, 12, 0, 0)
        ),
        RealtimeMessage(
            id=2, session_id=session_id, user_id=2, 
            message="안녕!", message_type=MessageType.TEXT,
            timestamp=datetime(2023, 1, 1, 12, 0, 5)
        )
    ]
    
    service.get_session_messages = MagicMock(return_value=mock_messages)
    
    # 실행
    result = service.export_conversation_as_text(session_id)
    
    # 검증
    expected = "[2023-01-01 12:00:00] 사용자1: 안녕하세요!\n[2023-01-01 12:00:05] 사용자2: 안녕!"
    assert result == expected


def test_export_conversation_as_text_empty(service, mock_db):
    """빈 대화 텍스트 변환 테스트"""
    session_id = 1
    
    service.get_session_messages = MagicMock(return_value=[])
    
    # 실행
    result = service.export_conversation_as_text(session_id)
    
    # 검증
    assert result == ""
