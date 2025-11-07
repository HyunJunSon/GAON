import pytest

from app.domains.auth import user_models, user_crud, user_schema
from app.core.security import verify_password


def test_create_user(db_session):
    """회원가입 테스트"""
    # 유효한 테스트 데이터 사용 - bcrypt 제한에 맞춤
    user_data = {
        "name": "testuser",  # 영어로만 구성 (한글/영어만 가능)
        "password": "TestPass1!",
        "confirmPassword": "TestPass1!",
        "email": "test@example.com"
    }
    
    # 사용자 생성
    user_create = user_schema.UserCreate(**user_data)
    user_crud.create_user(db=db_session, user_create=user_create)
    
    # 생성된 사용자 확인
    db_user = db_session.query(user_models.User).filter(user_models.User.name == "testuser").first()
    assert db_user is not None
    assert db_user.name == "testuser"
    assert db_user.email == "test@example.com"
    # 비밀번호가 해시되었는지 확인
    assert verify_password("TestPass1!", db_user.password)


def test_duplicate_email_fails(db_session):
    """동일 이메일로 회원가입 시도 시 실패하는지 테스트"""
    # 첫 번째 사용자 생성
    user_data = {
        "name": "testuser",  # 영어로만 구성 (한글/영어만 가능)
        "password": "TestPass1!",
        "confirmPassword": "TestPass1!",
        "email": "duplicate@example.com"
    }
    
    user_create = user_schema.UserCreate(**user_data)
    user_crud.create_user(db=db_session, user_create=user_create)
    
    # 두 번째 사용자 생성 - 동일 이메일 사용
    user_data2 = {
        "name": "testusertwo",  # 영어로만 구성 (한글/영어만 가능)
        "password": "Test2Pass@",
        "confirmPassword": "Test2Pass@",
        "email": "duplicate@example.com"  # 동일 이메일
    }
    
    user_create2 = user_schema.UserCreate(**user_data2)
    
    # 기존에 있는 이메일인지 확인
    existing_user = user_crud.get_existing_user(db=db_session, user_create=user_create2)
    assert existing_user is not None
    assert existing_user.email == "duplicate@example.com"


def test_password_validation():
    """비밀번호 유효성 검사 테스트"""
    # 유효한 비밀번호
    valid_password = "ValidPass1!"
    user_data = {
        "name": "testuser",
        "password": valid_password,
        "confirmPassword": valid_password,
        "email": "test@example.com"
    }
    
    user_create = user_schema.UserCreate(**user_data)
    # 스키마 레벨에서 검증에 성공해야 함
    assert user_create.password == valid_password


def test_invalid_password_fails():
    """유효하지 않은 비밀번호가 검증에 실패하는지 테스트"""
    # 유효하지 않은 비밀번호 (8자 미만)
    invalid_password = "Sh1!"
    
    with pytest.raises(ValueError):
        user_schema.UserCreate(
            name="testuser",
            password=invalid_password,
            confirmPassword=invalid_password,
            email="test@example.com"
        )


def test_create_user_via_api(client, db_session):
    """API를 통한 회원가입 테스트"""
    # 회원가입 요청
    response = client.post(
        "/api/auth/signup",
        json={
            "name": "apitestuser",
            "password": "ApiTestPass1!",
            "confirmPassword": "ApiTestPass1!",
            "email": "api@example.com"
        }
    )
    
    # 성공적으로 생성되었는지 확인 (204 No Content 예상)
    assert response.status_code == 204
    
    # 데이터베이스에 사용자가 생성되었는지 확인
    db_user = db_session.query(user_models.User).filter(user_models.User.name == "apitestuser").first()
    assert db_user is not None
    assert db_user.name == "apitestuser"
    assert db_user.email == "api@example.com"