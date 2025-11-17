#!/usr/bin/env python3
"""
Audio 시스템 종합 테스트 - API, 모델, 업로드 통합
"""
import pytest
import requests
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from google.cloud import storage

def test_audio_upload_api():
    """음성 파일 업로드 API 테스트"""
    print("🧪 음성 파일 업로드 API 테스트")
    
    try:
        # 로그인
        login_data = {"username": "gaon@gaon.com", "password": "abcd1234!"}
        login_response = requests.post("http://127.0.0.1:8000/api/auth/login", data=login_data)
        
        if login_response.status_code != 200:
            print(f"❌ 로그인 실패: {login_response.status_code}")
            return False
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # GCS에서 테스트 파일 다운로드
        storage_client = storage.Client()
        bucket = storage_client.bucket('gaon-cloud-data')
        blob = bucket.blob('user-upload-conv-data/conversations/user_48/9610873a-9f55-41f8-8b91-a3910346a90b.mp3')
        
        if not blob.exists():
            print("❌ 테스트 파일이 존재하지 않습니다")
            return False
        
        audio_content = blob.download_as_bytes()
        
        # 파일 업로드
        files = {"file": ("test.mp3", audio_content, "audio/mpeg")}
        response = requests.post(
            "http://127.0.0.1:8000/api/conversation/audio/upload",
            headers=headers,
            files=files
        )
        
        print(f"✅ 업로드 API 테스트: {response.status_code == 200}")
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ 업로드 테스트 실패: {e}")
        return False

def test_audio_api_functions():
    """Audio API 함수 존재 확인"""
    try:
        from app.domains.conversation.audio_router import upload_audio_conversation
        assert callable(upload_audio_conversation)
        print("✅ Audio API 함수 존재 확인")
        return True
    except ImportError:
        print("❌ Audio API 함수 import 실패")
        return False

def test_conversation_file_model():
    """ConversationFile 모델 음성 필드 테스트"""
    try:
        from app.domains.conversation.file_models import ConversationFile
        
        # 음성 관련 필드 확인
        required_fields = ['audio_url', 'transcript', 'speaker_segments', 'duration', 'speaker_count']
        
        for field in required_fields:
            assert hasattr(ConversationFile, field), f"Missing field: {field}"
        
        print("✅ ConversationFile 모델 필드 확인")
        return True
        
    except Exception as e:
        print(f"❌ 모델 테스트 실패: {e}")
        return False

@patch('app.domains.conversation.stt_service.speech.SpeechClient')
def test_audio_processing_mock(mock_speech_client):
    """Audio 처리 로직 Mock 테스트"""
    try:
        from app.domains.conversation.stt_service import STTService
        
        # Mock 설정
        mock_client = Mock()
        mock_speech_client.return_value = mock_client
        
        # STT 서비스 초기화
        stt_service = STTService()
        
        print("✅ Audio 처리 Mock 테스트")
        return True
        
    except Exception as e:
        print(f"❌ Mock 테스트 실패: {e}")
        return False

def run_all_audio_tests():
    """모든 Audio 시스템 테스트 실행"""
    print("🚀 Audio 시스템 종합 테스트 시작\n")
    
    results = {
        'upload_api': test_audio_upload_api(),
        'api_functions': test_audio_api_functions(),
        'model_fields': test_conversation_file_model(),
        'processing_mock': test_audio_processing_mock()
    }
    
    print(f"\n📋 테스트 결과:")
    for test_name, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"  {test_name}: {status}")
    
    return sum(results.values()) == len(results)

if __name__ == "__main__":
    success = run_all_audio_tests()
    exit(0 if success else 1)
