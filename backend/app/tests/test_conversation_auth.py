import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, AsyncMock
import io

from app.main import app
from app.core.database import get_db


# 테스트용 User 클래스 (id 필드 포함)
class MockUser:
    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email


@pytest.fixture
def mock_user():
    """테스트용 사용자 객체"""
    return MockUser(
        id=1,
        name="testuser",
        email="test@example.com"
    )


@pytest.fixture
def mock_db():
    """테스트용 DB 세션"""
    return Mock(spec=Session)


@pytest.fixture
def client_with_auth(mock_user, mock_db):
    """인증된 클라이언트"""
    def override_get_current_user():
        return mock_user
    
    def override_get_db():
        return mock_db
    
    app.dependency_overrides[get_db] = override_get_db
    from app.core.security import get_current_user
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    client = TestClient(app)
    yield client
    
    # 정리
    app.dependency_overrides.clear()


@patch('app.domains.conversation.router.ConversationFileService')
def test_upload_conversation_file_with_auth(mock_service_class, client_with_auth, mock_user):
    """JWT 인증을 통한 파일 업로드 테스트"""
    
    # 서비스 모킹
    mock_service = Mock()
    mock_service_class.return_value = mock_service
    
    # 반환값 설정
    mock_conversation = Mock()
    mock_conversation.id = 1
    mock_file = Mock()
    mock_file.id = 1
    mock_file.processing_status = "completed"
    mock_file.gcs_file_path = "test/gcs/path"
    
    # async 함수로 모킹
    mock_service.upload_file_and_create_conversation = AsyncMock(
        return_value=(mock_conversation, mock_file)
    )
    
    # 테스트 파일 생성
    test_file = io.BytesIO(b"test content")
    
    response = client_with_auth.post(
        "/api/conversations/analyze",
        files={"file": ("test.txt", test_file, "text/plain")},
        data={"family_id": "1"}
    )
    
    # 검증
    assert response.status_code == 200
    data = response.json()
    assert data["conversation_id"] == 1
    assert data["file_id"] == 1
    assert data["status"] == "completed"  # processing_status -> status로 변경
    
    # 서비스가 올바른 user_id로 호출되었는지 확인
    mock_service.upload_file_and_create_conversation.assert_called_once()
    call_args = mock_service.upload_file_and_create_conversation.call_args[0]
    assert call_args[0] == mock_user.id  # user_id가 JWT에서 추출된 값인지 확인


@patch('app.domains.conversation.router.ConversationFileService')
def test_get_user_files_with_auth(mock_service_class, client_with_auth, mock_user):
    """JWT 인증을 통한 사용자 파일 조회 테스트"""
    
    # 서비스 모킹
    mock_service = Mock()
    mock_service_class.return_value = mock_service
    mock_service.get_files_by_user_id.return_value = []
    
    response = client_with_auth.get("/api/conversations/files")
    
    # 검증
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    
    # 서비스가 올바른 user_id로 호출되었는지 확인
    mock_service.get_files_by_user_id.assert_called_once_with(mock_user.id)


def test_upload_without_auth():
    """인증 없이 파일 업로드 시도 테스트"""
    client = TestClient(app)
    
    test_file = io.BytesIO(b"test content")
    response = client.post(
        "/api/conversations/analyze",
        files={"file": ("test.txt", test_file, "text/plain")}
    )
    
    # 인증 실패로 401 응답 예상
    assert response.status_code == 401
