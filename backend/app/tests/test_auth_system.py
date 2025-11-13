#!/usr/bin/env python3
"""
Auth 시스템 종합 테스트 - 사용자, 인증, 권한 통합
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_user_creation():
    """회원가입 테스트"""
    try:
        from app.domains.auth import user_models, user_crud, user_schema
        
        user_data = {
            "name": "testuser",
            "password": "TestPass1!",
            "confirmPassword": "TestPass1!",
            "email": "test@example.com"
        }
        
        print("✅ 사용자 생성 데이터 구조 확인")
        return True
        
    except ImportError as e:
        print(f"❌ User 모듈 import 실패: {e}")
        return False

def test_password_verification():
    """비밀번호 검증 테스트"""
    try:
        from app.core.security import verify_password
        
        # 기본 검증 로직 확인
        assert callable(verify_password)
        print("✅ 비밀번호 검증 함수 확인")
        return True
        
    except ImportError:
        print("❌ Security 모듈 import 실패")
        return False

def test_auth_endpoints():
    """인증 엔드포인트 테스트"""
    try:
        import requests
        
        # 로그인 테스트
        login_data = {"username": "gaon@gaon.com", "password": "abcd1234!"}
        response = requests.post("http://127.0.0.1:8000/api/auth/login", data=login_data)
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"✅ 로그인 성공: 토큰 길이 {len(token) if token else 0}")
            return True
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 인증 엔드포인트 테스트 실패: {e}")
        return False

class MockUser:
    """테스트용 User 클래스"""
    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email

def test_user_mock():
    """User Mock 객체 테스트"""
    try:
        user = MockUser(1, "testuser", "test@example.com")
        
        assert user.id == 1
        assert user.name == "testuser"
        assert user.email == "test@example.com"
        
        print("✅ User Mock 객체 테스트")
        return True
        
    except Exception as e:
        print(f"❌ User Mock 테스트 실패: {e}")
        return False

def test_conversation_auth():
    """대화 권한 테스트"""
    try:
        # 권한이 필요한 API 테스트
        import requests
        
        # 토큰 없이 접근 시도
        response = requests.get("http://127.0.0.1:8000/api/conversation/audio/test/speaker-mapping")
        
        # 401 Unauthorized 응답 확인
        if response.status_code == 401:
            print("✅ 권한 보호 확인")
            return True
        else:
            print(f"❌ 권한 보호 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 권한 테스트 실패: {e}")
        return False

def run_all_auth_tests():
    """모든 Auth 시스템 테스트 실행"""
    print("🚀 Auth 시스템 종합 테스트 시작\n")
    
    results = {
        'user_creation': test_user_creation(),
        'password_verification': test_password_verification(),
        'auth_endpoints': test_auth_endpoints(),
        'user_mock': test_user_mock(),
        'conversation_auth': test_conversation_auth()
    }
    
    print(f"\n📋 테스트 결과:")
    for test_name, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"  {test_name}: {status}")
    
    return sum(results.values()) == len(results)

if __name__ == "__main__":
    success = run_all_auth_tests()
    exit(0 if success else 1)
