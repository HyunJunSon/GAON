import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, AsyncMock
import io

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
def test_upload_response_structure(mock_service_class, client_with_auth, mock_user):
    """파일 업로드 응답 구조 테스트"""
    
    # 서비스 모킹
    mock_service = Mock()
    mock_service_class.return_value = mock_service
    
    # 반환값 설정
    mock_conversation = Mock()
    mock_conversation.id = 123
    mock_file = Mock()
    mock_file.id = 456
    mock_file.processing_status = "completed"
    mock_file.gcs_file_path = "test/gcs/path"
    
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
    
    # 응답 구조 검증
    assert response.status_code == 200
    data = response.json()
    
    # 필수 필드 확인
    assert "conversation_id" in data
    assert "file_id" in data
    assert "status" in data
    assert "message" in data
    
    # 값 확인
    assert data["conversation_id"] == 123
    assert data["file_id"] == 456
    assert data["status"] == "completed"
    assert data["message"] == "파일이 성공적으로 업로드되고 처리되었습니다."
    
    # 선택적 필드 확인
    if "gcs_file_path" in data:
        assert data["gcs_file_path"] == "test/gcs/path"


def test_formdata_structure():
    """FormData 구조 테스트"""
    # 프론트엔드에서 보내는 FormData 구조 시뮬레이션
    form_data = {
        "file": "test_file_content",
        "family_id": "1"  # 선택적 파라미터
    }
    
    # 필수 필드 확인
    assert "file" in form_data
    
    # 선택적 필드는 있을 수도 없을 수도 있음
    family_id = form_data.get("family_id")
    if family_id is not None:
        assert isinstance(family_id, str)  # FormData는 문자열로 전송됨


def test_response_field_naming():
    """응답 필드 명명 규칙 테스트"""
    from app.domains.conversation.schemas import FileUploadResponse
    
    # Pydantic 모델 필드 확인
    fields = FileUploadResponse.model_fields
    
    # snake_case 필드 확인
    assert "conversation_id" in fields
    assert "file_id" in fields
    assert "status" in fields
    assert "message" in fields
    
    # 이전 필드명이 없는지 확인
    assert "processing_status" not in fields
