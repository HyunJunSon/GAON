import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import timedelta
import json

# Add the app directory to the path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.database import Base, get_db
from app.domains.auth import user_models
from app.domains.auth.new_user_crud import new_create_user, new_get_existing_user, new_authenticate_user, pwd_context
from app.domains.auth.new_user_schema import NewUserCreate, NewToken, NewUserDelete
from app.core.new_security import new_create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

# Import all models to ensure they are registered with Base.metadata
from app.domains.conversation import models as conversation_models
from app.domains.family import models as family_models


# 테스트용 인-메모리 SQLite 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 테스트용 데이터베이스 생성
Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.drop_all(bind=engine)  # Drop all tables
    Base.metadata.create_all(bind=engine) # Recreate all tables
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        # Dependency override for database session
        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()
        app.dependency_overrides[get_db] = override_get_db
        yield test_client
        app.dependency_overrides.clear() # Clean up overrides


@pytest.fixture
def setup_new_test_user(db_session):
    email = "new_test@example.com"
    password = "password123!"
    user_data = {
        "name": "newtestuser",
        "password": password,
        "confirmPassword": password,
        "email": email
    }
    user_create = NewUserCreate(**user_data)
    new_create_user(db=db_session, user_create=user_create)
    return email, password


def test_new_create_user(db_session):
    """새로운 회원가입 테스트"""
    user_data = {
        "name": "newuser_test",
        "password": "password123!",
        "confirmPassword": "password123!",
        "email": "new_user@example.com"
    }
    user_create = NewUserCreate(**user_data)
    new_create_user(db=db_session, user_create=user_create)
    
    db_user = db_session.query(user_models.User).filter(user_models.User.name == "newuser_test").first()
    assert db_user is not None
    assert db_user.name == "newuser_test"
    assert db_user.email == "new_user@example.com"
    assert pwd_context.verify("password123!".encode('utf-8'), db_user.password)


def test_new_duplicate_email_fails(db_session):
    """새로운 동일 이메일로 회원가입 시도 시 실패하는지 테스트"""
    user_data = {
        "name": "newdupuser",
        "password": "password123!",
        "confirmPassword": "password123!",
        "email": "new_duplicate@example.com"
    }
    new_create_user(db=db_session, user_create=NewUserCreate(**user_data))
    
    user_data2 = {
        "name": "newdupuser2",
        "password": "password123!",
        "confirmPassword": "password123!",
        "email": "new_duplicate@example.com"
    }
    existing_user = new_get_existing_user(db=db_session, user_create=NewUserCreate(**user_data2))
    assert existing_user is not None
    assert existing_user.email == "new_duplicate@example.com"


def test_new_login_success(client, setup_new_test_user):
    """새로운 로그인 성공 테스트"""
    email, password = setup_new_test_user
    response = client.post(
        "/api/new_auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()


def test_new_login_fail_wrong_password(client, setup_new_test_user):
    """새로운 잘못된 비밀번호로 로그인 실패 테스트"""
    email, _ = setup_new_test_user
    response = client.post(
        "/api/new_auth/login",
        data={
            "username": email,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "잘못된 자격 증명입니다."}


def test_new_login_fail_non_existent_user(client):
    """새로운 존재하지 않는 사용자로 로그인 실패 테스트"""
    response = client.post(
        "/api/new_auth/login",
        data={
            "username": "nonexistent_new@example.com",
            "password": "anypassword"
        }
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "잘못된 자격 증명입니다."}


def test_new_delete_user_success(client, db_session, setup_new_test_user):
    """새로운 회원 탈퇴 성공 테스트"""
    email, password = setup_new_test_user
    
    login_response = client.post(
        "/api/new_auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    delete_response = client.request(
        "DELETE",
        "/api/new_auth/user",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "password": password
        }
    )
    assert delete_response.status_code == 204

    db_user = db_session.query(user_models.User).filter(user_models.User.email == email).first()
    assert db_user is None


def test_new_delete_user_fail_wrong_password(client, db_session, setup_new_test_user):
    """새로운 잘못된 비밀번호로 회원 탈퇴 실패 테스트"""
    email, password = setup_new_test_user
    
    login_response = client.post(
        "/api/new_auth/login",
        data={
            "username": email,
            "password": password
        }
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    delete_response = client.request(
        "DELETE",
        "/api/new_auth/user",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "password": "wrongpassword"
        }
    )
    assert delete_response.status_code == 401
    assert delete_response.json() == {"detail": "잘못된 자격 증명입니다."}

    db_user = db_session.query(user_models.User).filter(user_models.User.email == email).first()
    assert db_user is not None


def test_new_delete_user_fail_unauthenticated(client, db_session, setup_new_test_user):
    """새로운 인증되지 않은 상태로 회원 탈퇴 실패 테스트"""
    email, _ = setup_new_test_user
    
    delete_response = client.request(
        "DELETE",
        "/api/new_auth/user",
        json={
            "password": "anypassword"
        }
    )
    assert delete_response.status_code == 401
    assert delete_response.json() == {"detail": "Not authenticated"}

    db_user = db_session.query(user_models.User).filter(user_models.User.email == email).first()
    assert db_user is not None
