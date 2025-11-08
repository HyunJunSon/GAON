import pytest
from unittest.mock import AsyncMock, MagicMock
from app.domains.conversation.websocket_manager import ConnectionManager


@pytest.fixture
def manager():
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


@pytest.mark.asyncio
async def test_connect_user(manager, mock_websocket):
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


def test_disconnect_user(manager, mock_websocket):
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


def test_get_room_users(manager, mock_websocket):
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


def test_get_room_users_empty_room(manager):
    """빈 방 사용자 목록 조회 테스트"""
    users = manager.get_room_users("nonexistent_room")
    assert users == []
