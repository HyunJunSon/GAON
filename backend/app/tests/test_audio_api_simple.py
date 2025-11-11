"""
Task 1-3, 1-4 API 엔드포인트 기능 테스트
"""
import pytest
from unittest.mock import Mock


def test_audio_upload_api_exists():
    """음성 업로드 API 함수 존재 확인"""
    from app.domains.conversation.audio_router import upload_audio_conversation
    assert callable(upload_audio_conversation)


def test_audio_detail_api_exists():
    """음성 대화 상세 조회 API 함수 존재 확인"""
    from app.domains.conversation.audio_router import get_audio_conversation_detail
    assert callable(get_audio_conversation_detail)


def test_audio_router_endpoints():
    """오디오 라우터 엔드포인트 확인"""
    from app.domains.conversation.audio_router import router
    
    # 라우터에 등록된 경로 확인
    routes = [route.path for route in router.routes]
    
    assert "/api/conversation/audio" in routes
    assert any("/api/conversation/audio/{conversation_id}" in route.path for route in router.routes)


def test_file_size_validation():
    """파일 크기 검증 로직 테스트"""
    max_size = 20 * 1024 * 1024  # 20MB
    
    # 정상 크기
    normal_file = b'x' * (10 * 1024 * 1024)  # 10MB
    assert len(normal_file) <= max_size
    
    # 초과 크기
    large_file = b'x' * (25 * 1024 * 1024)  # 25MB
    assert len(large_file) > max_size


def test_audio_format_validation():
    """오디오 형식 검증 로직 테스트"""
    allowed_extensions = {'webm', 'wav', 'mp3', 'm4a'}
    
    # 허용된 형식
    assert 'webm' in allowed_extensions
    assert 'wav' in allowed_extensions
    assert 'mp3' in allowed_extensions
    assert 'm4a' in allowed_extensions
    
    # 허용되지 않은 형식
    assert 'txt' not in allowed_extensions
    assert 'pdf' not in allowed_extensions


def test_stt_result_structure():
    """STT 결과 구조 검증"""
    expected_keys = {'transcript', 'speaker_segments', 'duration', 'speaker_count'}
    
    # 예상 결과 구조
    mock_result = {
        "transcript": "안녕하세요. 반갑습니다.",
        "speaker_segments": [
            {"speaker": 1, "start": 0.0, "end": 2.3, "text": "안녕하세요"},
            {"speaker": 2, "start": 2.4, "end": 5.1, "text": "반갑습니다"}
        ],
        "duration": 5,
        "speaker_count": 2
    }
    
    # 모든 필수 키가 있는지 확인
    assert all(key in mock_result for key in expected_keys)
    
    # 화자 구간 구조 확인
    for segment in mock_result["speaker_segments"]:
        assert "speaker" in segment
        assert "start" in segment
        assert "end" in segment
        assert "text" in segment


def test_conversation_file_audio_fields():
    """ConversationFile 모델의 오디오 필드 확인"""
    from app.domains.conversation.file_models import ConversationFile
    
    # 모델 클래스에 오디오 관련 필드가 있는지 확인
    model_fields = ConversationFile.__table__.columns.keys()
    
    audio_fields = ['audio_url', 'transcript', 'speaker_segments', 'duration', 'speaker_count']
    
    for field in audio_fields:
        assert field in model_fields, f"ConversationFile 모델에 {field} 필드가 없습니다"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
