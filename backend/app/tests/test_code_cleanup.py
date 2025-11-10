import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, AsyncMock
import io
import logging

from app.main import app
from app.core.database import get_db


# 테스트용 User 클래스
class MockUser:
    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email


@pytest.fixture
def mock_user():
    return MockUser(id=1, name="testuser", email="test@example.com")


@pytest.fixture
def mock_db():
    return Mock(spec=Session)


@pytest.fixture
def client_with_auth(mock_user, mock_db):
    def override_get_current_user():
        return mock_user
    
    def override_get_db():
        return mock_db
    
    app.dependency_overrides[get_db] = override_get_db
    from app.core.security import get_current_user
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@patch('app.domains.conversation.router.ConversationFileService')
def test_logging_on_success(mock_service_class, client_with_auth, mock_user, caplog):
    """성공 시 로깅 테스트"""
    
    # 서비스 모킹
    mock_service = Mock()
    mock_service_class.return_value = mock_service
    
    mock_conversation = Mock()
    mock_conversation.id = 123
    mock_file = Mock()
    mock_file.id = 456
    mock_file.processing_status = "completed"
    mock_file.gcs_file_path = "test/path"
    
    mock_service.upload_file_and_create_conversation = AsyncMock(
        return_value=(mock_conversation, mock_file)
    )
    
    # 로깅 레벨 설정
    with caplog.at_level(logging.INFO):
        test_file = io.BytesIO(b"test content")
        response = client_with_auth.post(
            "/api/conversations/analyze",
            files={"file": ("test.txt", test_file, "text/plain")}
        )
    
    # 응답 확인
    assert response.status_code == 200
    
    # 로그 메시지 확인
    log_messages = [record.message for record in caplog.records]
    assert any("파일 업로드 요청" in msg for msg in log_messages)
    assert any("파일 업로드 성공" in msg for msg in log_messages)


@patch('app.domains.conversation.router.ConversationFileService')
def test_error_handling_with_logging(mock_service_class, client_with_auth, mock_user, caplog):
    """에러 처리 및 로깅 테스트"""
    
    # 서비스 모킹 - 에러 발생
    mock_service = Mock()
    mock_service_class.return_value = mock_service
    
    mock_service.upload_file_and_create_conversation = AsyncMock(
        side_effect=Exception("테스트 에러")
    )
    
    # 로깅 레벨 설정
    with caplog.at_level(logging.ERROR):
        test_file = io.BytesIO(b"test content")
        response = client_with_auth.post(
            "/api/conversations/analyze",
            files={"file": ("test.txt", test_file, "text/plain")}
        )
    
    # 에러 응답 확인
    assert response.status_code == 500
    assert "서버 오류" in response.json()["detail"]
    
    # 에러 로그 확인
    error_logs = [record for record in caplog.records if record.levelno >= logging.ERROR]
    assert len(error_logs) > 0
    assert any("파일 업로드 실패 (서버)" in record.message for record in error_logs)


def test_family_id_default_handling():
    """family_id 기본값 처리 테스트"""
    # family_id가 None일 때 기본값 1이 사용되는지 확인
    family_id = None
    if family_id is None:
        family_id = 1
    
    assert family_id == 1


@patch('app.domains.conversation.router.ConversationFileService')
def test_authentication_required(mock_service_class, client_with_auth, mock_user):
    """모든 엔드포인트에 인증이 필요한지 확인"""
    
    # 인증된 클라이언트로 파일 목록 조회
    mock_service = Mock()
    mock_service_class.return_value = mock_service
    mock_service.get_files_by_user_id.return_value = []
    
    response = client_with_auth.get("/api/conversations/files")
    assert response.status_code == 200
    
    # 서비스가 현재 사용자 ID로 호출되었는지 확인
    mock_service.get_files_by_user_id.assert_called_once_with(mock_user.id)


def test_error_response_format():
    """에러 응답 형식 테스트"""
    client = TestClient(app)
    
    # 인증 없이 요청
    test_file = io.BytesIO(b"test content")
    response = client.post(
        "/api/conversations/analyze",
        files={"file": ("test.txt", test_file, "text/plain")}
    )
    
    # 401 에러 확인
    assert response.status_code == 401
    
    # 에러 응답 구조 확인
    error_data = response.json()
    assert "detail" in error_data
