
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app  # main.py에서 FastAPI app을 가져옵니다.
from app.core.database import Base, get_db
from app.domains.auth.user_models import User
from app.core.security import hash_password

# 이 테스트 모듈의 모든 테스트 전에 테스트 유저를 생성하는 fixture
@pytest.fixture(scope="function")
def setup_test_user(db_session):
    # 기존 유저가 있다면 삭제
    db_session.query(User).delete()
    
    # 테스트용 유저 생성
    test_user = User(
        email="test@example.com",
        password=hash_password("Test@123password"),
        name="테스트유저",
        create_date=datetime.now(),
    )
    db_session.add(test_user)
    db_session.commit()


def test_login_for_access_token_success(client, setup_test_user):
    """
    로그인 성공 테스트
    """
    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "Test@123password"},
    )
    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"
    assert json_response["username"] == "test@example.com"


def test_login_for_access_token_failure_wrong_password(client, setup_test_user):
    """
    로그인 실패 테스트 (잘못된 비밀번호)
    """
    response = client.post(
        "/api/auth/login",
        data={"username": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    json_response = response.json()
    assert json_response["detail"] == "이메일 또는 비밀번호가 잘못되었습니다."


def test_login_for_access_token_failure_wrong_username(client, setup_test_user):
    """
    로그인 실패 테스트 (존재하지 않는 사용자)
    """
    response = client.post(
        "/api/auth/login",
        data={"username": "wrong@example.com", "password": "Test@123password"},
    )
    assert response.status_code == 401
    json_response = response.json()
    assert json_response["detail"] == "이메일 또는 비밀번호가 잘못되었습니다."

