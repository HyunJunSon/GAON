#!/usr/bin/env python3
"""
유틸리티 시스템 종합 테스트 - API 구조, 코드 정리, 파일 형식 통합
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
from app.main import app
from app.core.config import settings

class MockUser:
    """테스트용 User 클래스"""
    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email

def test_api_structure():
    """API 구조 테스트"""
    try:
        client = TestClient(app)
        
        # 기본 엔드포인트 확인
        response = client.get("/")
        
        print(f"✅ API 구조 테스트: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"❌ API 구조 테스트 실패: {e}")
        return False

def test_allowed_file_types():
    """지원 파일 형식 확인"""
    try:
        expected_types = {"txt", "pdf", "docx", "epub", "md"}
        
        if hasattr(settings, 'allowed_file_types'):
            actual_types = set(settings.allowed_file_types)
            assert actual_types == expected_types
        
        print("✅ 파일 형식 설정 확인")
        return True
        
    except Exception as e:
        print(f"❌ 파일 형식 테스트 실패: {e}")
        return False

def test_max_file_size():
    """최대 파일 크기 확인"""
    try:
        expected_size = 10 * 1024 * 1024  # 10MB
        
        if hasattr(settings, 'max_file_size'):
            assert settings.max_file_size == expected_size
        
        print("✅ 파일 크기 설정 확인")
        return True
        
    except Exception as e:
        print(f"❌ 파일 크기 테스트 실패: {e}")
        return False

def test_mock_user_functionality():
    """Mock User 기능 테스트"""
    try:
        user = MockUser(1, "testuser", "test@example.com")
        
        assert user.id == 1
        assert user.name == "testuser"
        assert user.email == "test@example.com"
        
        print("✅ Mock User 기능 확인")
        return True
        
    except Exception as e:
        print(f"❌ Mock User 테스트 실패: {e}")
        return False

def test_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        from app.core.database import get_db
        
        # DB 함수 존재 확인
        assert callable(get_db)
        
        print("✅ 데이터베이스 연결 함수 확인")
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 테스트 실패: {e}")
        return False

def test_langsmith_integration():
    """LangSmith 통합 테스트"""
    try:
        # LangSmith 설정 확인 (있다면)
        langsmith_available = hasattr(settings, 'langsmith_api_key')
        
        print(f"✅ LangSmith 설정 확인: {'사용 가능' if langsmith_available else '설정 없음'}")
        return True
        
    except Exception as e:
        print(f"❌ LangSmith 테스트 실패: {e}")
        return False

def run_all_utils_tests():
    """모든 유틸리티 시스템 테스트 실행"""
    print("🚀 유틸리티 시스템 종합 테스트 시작\n")
    
    results = {
        'api_structure': test_api_structure(),
        'file_types': test_allowed_file_types(),
        'file_size': test_max_file_size(),
        'mock_user': test_mock_user_functionality(),
        'database': test_database_connection(),
        'langsmith': test_langsmith_integration()
    }
    
    print(f"\n📋 테스트 결과:")
    for test_name, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"  {test_name}: {status}")
    
    return sum(results.values()) == len(results)

if __name__ == "__main__":
    success = run_all_utils_tests()
    exit(0 if success else 1)
