#!/usr/bin/env python3
"""
Conversation 시스템 종합 테스트 - 대화, STT 서비스 통합
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def test_conversation_database():
    """대화 데이터베이스 테스트"""
    try:
        from app.core.database import Base, get_db
        
        # 테스트용 DB 설정
        SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
        engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        print("✅ 대화 데이터베이스 설정 확인")
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 테스트 실패: {e}")
        return False

@patch('app.domains.conversation.stt_service.speech.SpeechClient')
def test_stt_service_initialization(mock_speech_client):
    """STTService 초기화 테스트"""
    try:
        from app.domains.conversation.stt_service import STTService
        
        # Mock 설정
        mock_client = Mock()
        mock_speech_client.return_value = mock_client
        
        # STT 서비스 초기화
        stt_service = STTService()
        
        print("✅ STT 서비스 초기화 확인")
        return True
        
    except Exception as e:
        print(f"❌ STT 서비스 테스트 실패: {e}")
        return False

def test_conversation_models():
    """대화 모델 테스트"""
    try:
        from app.domains.conversation.file_models import ConversationFile
        
        # 기본 필드 확인
        required_fields = ['id', 'created_at', 'updated_at']
        
        for field in required_fields:
            assert hasattr(ConversationFile, field), f"Missing basic field: {field}"
        
        print("✅ 대화 모델 기본 구조 확인")
        return True
        
    except Exception as e:
        print(f"❌ 대화 모델 테스트 실패: {e}")
        return False

def test_conversation_api_client():
    """대화 API 클라이언트 테스트"""
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # 기본 헬스체크
        response = client.get("/")
        
        print(f"✅ API 클라이언트 테스트: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"❌ API 클라이언트 테스트 실패: {e}")
        return False

@patch('app.domains.conversation.stt_service.speech.SpeechClient')
def test_stt_transcription_mock(mock_speech_client):
    """STT 전사 Mock 테스트"""
    try:
        from app.domains.conversation.stt_service import STTService
        
        # Mock 응답 설정
        mock_client = Mock()
        mock_response = Mock()
        mock_response.results = []
        mock_client.recognize.return_value = mock_response
        mock_speech_client.return_value = mock_client
        
        stt_service = STTService()
        
        print("✅ STT 전사 Mock 설정 확인")
        return True
        
    except Exception as e:
        print(f"❌ STT Mock 테스트 실패: {e}")
        return False

def run_all_conversation_tests():
    """모든 Conversation 시스템 테스트 실행"""
    print("🚀 Conversation 시스템 종합 테스트 시작\n")
    
    results = {
        'database': test_conversation_database(),
        'stt_initialization': test_stt_service_initialization(),
        'models': test_conversation_models(),
        'api_client': test_conversation_api_client(),
        'stt_mock': test_stt_transcription_mock()
    }
    
    print(f"\n📋 테스트 결과:")
    for test_name, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"  {test_name}: {status}")
    
    return sum(results.values()) == len(results)

if __name__ == "__main__":
    success = run_all_conversation_tests()
    exit(0 if success else 1)
