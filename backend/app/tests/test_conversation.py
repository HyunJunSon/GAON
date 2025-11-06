import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db

# 테스트용 인메모리 DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# 테스트 클라이언트
client = TestClient(app)

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_health_check():
    """헬스체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "가온" in response.json()["message"]

@patch('app.domains.conversation.file_processor.storage.Client')
def test_upload_real_conversation_file(mock_storage_client, setup_database):
    """실제 대화 파일 업로드 테스트 (GCS 모킹)"""
    # GCS 클라이언트 모킹
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    
    mock_storage_client.return_value = mock_client
    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    
    test_file_path = "/Users/hyunjunson/Project/GAON/backend/app/tests/test-raw/resource_depression_1_check_D002.txt"
    
    # 파일 존재 확인
    assert os.path.exists(test_file_path), f"테스트 파일이 존재하지 않습니다: {test_file_path}"
    
    with open(test_file_path, 'rb') as f:
        response = client.post(
            "/api/conversations/analyze",
            params={"user_id": 1, "family_id": 1},
            files={"file": ("resource_depression_1_check_D002.txt", f, "text/plain")}
        )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "file_id" in data
    assert data["processing_status"] == "completed"
    
    # GCS 업로드가 호출되었는지 확인
    mock_blob.upload_from_string.assert_called_once()
    
    return data["conversation_id"]

@patch('app.domains.conversation.file_processor.storage.Client')
def test_get_analysis_with_real_file(mock_storage_client, setup_database):
    """실제 파일로 분석 결과 조회 테스트"""
    # GCS 클라이언트 모킹
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    
    mock_storage_client.return_value = mock_client
    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    
    test_file_path = "/Users/hyunjunson/Project/GAON/backend/app/tests/test-raw/resource_depression_1_check_D002.txt"
    
    # 파일 업로드
    with open(test_file_path, 'rb') as f:
        upload_response = client.post(
            "/api/conversations/analyze",
            params={"user_id": 1, "family_id": 1},
            files={"file": ("resource_depression_1_check_D002.txt", f, "text/plain")}
        )
    
    conversation_id = upload_response.json()["conversation_id"]
    
    # 분석 결과 조회
    analysis_response = client.get(f"/api/analysis/{conversation_id}")
    
    print(f"Analysis response: {analysis_response.json()}")
    
    assert analysis_response.status_code == 200
    data = analysis_response.json()
    assert "summary" in data
    assert "emotion" in data
    assert "dialog" in data
    assert "status" in data
    assert data["status"] == "completed"

@patch('app.domains.conversation.file_processor.storage.Client')
def test_upload_invalid_file_type(mock_storage_client, setup_database):
    """지원하지 않는 파일 형식 테스트"""
    from io import BytesIO
    file_data = BytesIO(b"invalid content")
    
    response = client.post(
        "/api/conversations/analyze",
        params={"user_id": 1, "family_id": 1},
        files={"file": ("test.exe", file_data, "application/octet-stream")}
    )
    
    assert response.status_code == 400
    assert "지원하지 않는 파일 형식" in response.json()["detail"]

@patch('app.domains.conversation.file_processor.storage.Client')
def test_get_nonexistent_analysis(mock_storage_client, setup_database):
    """존재하지 않는 conversation 분석 조회 테스트"""
    response = client.get("/api/analysis/99999")
    
    assert response.status_code == 404
    assert "대화를 찾을 수 없습니다" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
