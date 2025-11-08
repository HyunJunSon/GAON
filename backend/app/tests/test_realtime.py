import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from app.main import app
from app.domains.conversation.realtime_models import RealtimeSession, RealtimeMessage, SessionStatus, MessageType
from app.domains.conversation.realtime_services import RealtimeService
from app.domains.conversation.websocket_manager import ConnectionManager


client = TestClient(app)


# ===== 모델 테스트 =====
class TestRealtimeModels:
    def test_realtime_session_creation(self):
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

    def test_realtime_message_creation(self):
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

    def test_session_status_enum(self):
        """SessionStatus enum 테스트"""
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.ENDED.value == "ended"

    def test_message_type_enum(self):
        """MessageType enum 테스트"""
        assert MessageType.TEXT.value == "text"
        assert MessageType.SYSTEM.value == "system"


# ===== WebSocket 매니저 테스트 =====
class TestWebSocketManager:
    @pytest.fixture
    def manager(self):
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_user(self, manager, mock_websocket):
        """사용자 연결 테스트"""
        room_id = "test_room"
        user_id = 1
        family_id = 1
        
        await manager.connect(mock_websocket, room_id, user_id, family_id)
        
        # WebSocket accept 호출 확인
        mock_websocket.accept.assert_called_once()
        
        # 연결 정보 저장 확인
        assert room_id in manager.active_connections
        assert mock_websocket in manager.active_connections[room_id]
        assert mock_websocket in manager.user_info
        assert manager.user_info[mock_websocket]["user_id"] == user_id

    def test_disconnect_user(self, manager, mock_websocket):
        """사용자 연결 해제 테스트"""
        # 먼저 연결
        manager.active_connections["test_room"] = [mock_websocket]
        manager.user_info[mock_websocket] = {
            "user_id": 1,
            "family_id": 1,
            "room_id": "test_room"
        }
        
        # 연결 해제
        manager.disconnect(mock_websocket)
        
        # 연결 정보 제거 확인
        assert "test_room" not in manager.active_connections
        assert mock_websocket not in manager.user_info

    def test_get_room_users(self, manager, mock_websocket):
        """방 사용자 목록 조회 테스트"""
        room_id = "test_room"
        user_id = 1
        
        # 연결 정보 설정
        manager.active_connections[room_id] = [mock_websocket]
        manager.user_info[mock_websocket] = {
            "user_id": user_id,
            "family_id": 1,
            "room_id": room_id
        }
        
        users = manager.get_room_users(room_id)
        assert users == [user_id]

    def test_get_room_users_empty_room(self, manager):
        """빈 방 사용자 목록 조회 테스트"""
        users = manager.get_room_users("nonexistent_room")
        assert users == []


# ===== 서비스 테스트 =====
class TestRealtimeService:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return RealtimeService(mock_db)

    def test_create_session(self, service, mock_db):
        """세션 생성 테스트"""
        family_id = 1
        
        # Mock 설정
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # 실행
        result = service.create_session(family_id)
        
        # 검증
        assert result.family_id == family_id
        assert result.status == SessionStatus.ACTIVE
        assert result.room_id.startswith("room_")
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_save_message(self, service, mock_db):
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

    def test_export_conversation_as_text(self, service):
        """대화 텍스트 변환 테스트"""
        session_id = 1
        
        # Mock 메시지들
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


# ===== API 라우터 테스트 =====
class TestRealtimeRouter:
    @patch('app.domains.conversation.realtime_router.get_db')
    def test_create_realtime_session(self, mock_get_db):
        """실시간 세션 생성 API 테스트"""
        # Mock DB 설정
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock 세션
        mock_session = RealtimeSession(
            id=1,
            room_id="room_12345678",
            family_id=1,
            status=SessionStatus.ACTIVE
        )
        mock_session.created_at = datetime(2023, 1, 1, 12, 0, 0)
        mock_session.ended_at = None
        
        with patch('app.domains.conversation.realtime_router.RealtimeService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.create_session.return_value = mock_session
            
            # API 호출
            response = client.post("/api/conversations/realtime/sessions?family_id=1")
            
            # 검증
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["room_id"] == "room_12345678"
            assert data["family_id"] == 1
            assert data["status"] == "active"

    @patch('app.domains.conversation.realtime_router.get_db')
    def test_end_session(self, mock_get_db):
        """세션 종료 API 테스트"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_session = RealtimeSession(
            id=1,
            room_id="room_12345678",
            family_id=1,
            status=SessionStatus.ENDED
        )
        
        with patch('app.domains.conversation.realtime_router.RealtimeService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.end_session.return_value = mock_session
            
            response = client.post("/api/conversations/realtime/sessions/room_12345678/end")
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Session ended successfully"
            assert data["session_id"] == 1

    @patch('app.domains.conversation.realtime_router.get_db')
    def test_export_conversation(self, mock_get_db):
        """대화 내보내기 API 테스트"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        mock_session = RealtimeSession(
            id=1,
            room_id="room_12345678",
            family_id=1,
            status=SessionStatus.ENDED
        )
        
        with patch('app.domains.conversation.realtime_router.RealtimeService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            mock_service.get_session_by_room_id.return_value = mock_session
            mock_service.export_conversation_as_text.return_value = "대화 내용"
            mock_service.get_session_messages.return_value = [1, 2, 3]
            
            response = client.get("/api/conversations/realtime/sessions/room_12345678/export")
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == 1
            assert data["conversation_text"] == "대화 내용"
            assert data["message_count"] == 3
