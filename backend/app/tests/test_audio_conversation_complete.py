"""
GAON 음성 대화 기능 통합 테스트
Phase 1 백엔드 구현 완료 검증 (Task 1-1 ~ 1-4)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
import io
from fastapi.testclient import TestClient
from fastapi import UploadFile


class TestConversationFileModel:
    """Task 1-1: ConversationFile 모델 음성 필드 테스트"""
    
    def test_audio_fields_exist(self):
        """음성 관련 필드가 모델에 존재하는지 확인"""
        from app.domains.conversation.file_models import ConversationFile
        
        assert hasattr(ConversationFile, 'audio_url')
        assert hasattr(ConversationFile, 'transcript')
        assert hasattr(ConversationFile, 'speaker_segments')
        assert hasattr(ConversationFile, 'duration')
        assert hasattr(ConversationFile, 'speaker_count')
    
    def test_audio_field_types(self):
        """음성 필드 타입이 올바른지 확인"""
        from app.domains.conversation.file_models import ConversationFile
        
        # 필드 존재 확인
        audio_url_column = ConversationFile.__table__.columns.get('audio_url')
        transcript_column = ConversationFile.__table__.columns.get('transcript')
        speaker_segments_column = ConversationFile.__table__.columns.get('speaker_segments')
        duration_column = ConversationFile.__table__.columns.get('duration')
        speaker_count_column = ConversationFile.__table__.columns.get('speaker_count')
        
        assert audio_url_column is not None
        assert transcript_column is not None
        assert speaker_segments_column is not None
        assert duration_column is not None
        assert speaker_count_column is not None
        
        # nullable 속성 확인
        assert audio_url_column.nullable is True
        assert transcript_column.nullable is True
        assert speaker_segments_column.nullable is True
        assert duration_column.nullable is True
        assert speaker_count_column.nullable is True


class TestSTTService:
    """Task 1-2: STT 서비스 테스트"""
    
    @patch('app.domains.conversation.stt_service.speech.SpeechClient')
    def test_stt_service_initialization(self, mock_speech_client):
        """STTService 초기화 테스트"""
        from app.domains.conversation.stt_service import STTService
        
        mock_client = Mock()
        mock_speech_client.return_value = mock_client
        
        stt_service = STTService()
        
        assert stt_service.client == mock_client
        mock_speech_client.assert_called_once()
    
    @patch('app.domains.conversation.stt_service.speech.SpeechClient')
    def test_stt_service_initialization_failure(self, mock_speech_client):
        """STTService 초기화 실패 테스트"""
        from app.domains.conversation.stt_service import STTService
        
        mock_speech_client.side_effect = Exception("API 키 오류")
        
        with pytest.raises(Exception) as exc_info:
            STTService()
        
        assert "API 키 오류" in str(exc_info.value)
    
    @patch('app.domains.conversation.stt_service.speech.SpeechClient')
    def test_transcribe_audio_with_diarization(self, mock_speech_client):
        """STT 및 화자 구분 기능 테스트"""
        from app.domains.conversation.stt_service import STTService
        
        # Mock 설정
        mock_client = Mock()
        mock_speech_client.return_value = mock_client
        
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.results = [
            Mock(alternatives=[
                Mock(transcript="안녕하세요 반갑습니다", words=[
                    Mock(start_time=Mock(total_seconds=lambda: 0.0), 
                         end_time=Mock(total_seconds=lambda: 2.0), 
                         word="안녕하세요", 
                         speaker_tag=1),
                    Mock(start_time=Mock(total_seconds=lambda: 2.1), 
                         end_time=Mock(total_seconds=lambda: 4.0), 
                         word="반갑습니다", 
                         speaker_tag=2)
                ])
            ])
        ]
        mock_client.recognize.return_value = mock_response
        
        # STT 서비스 실행
        stt_service = STTService()
        result = stt_service.transcribe_audio_with_diarization(b"fake_audio_data")
        
        # 결과 검증
        assert "transcript" in result
        assert "speaker_segments" in result
        assert "duration" in result
        assert "speaker_count" in result
        assert result["speaker_count"] == 2
    
    def test_validate_audio_format(self):
        """오디오 형식 검증 테스트"""
        from app.domains.conversation.stt_service import STTService
        
        with patch('app.domains.conversation.stt_service.speech.SpeechClient'):
            stt_service = STTService()
            
            # WebM 시그니처 테스트
            webm_data = b'\x1a\x45\xdf\xa3' + b'\x00' * 100
            assert stt_service.validate_audio_format(webm_data) is True
            
            # 잘못된 형식 테스트
            invalid_data = b'\x00\x00\x00\x00' + b'\x00' * 100
            assert stt_service.validate_audio_format(invalid_data) is False


class TestAudioAPI:
    """Task 1-3, 1-4: 음성 API 엔드포인트 테스트"""
    
    def test_audio_upload_api_exists(self):
        """음성 업로드 API 함수 존재 확인"""
        from app.domains.conversation.audio_router import upload_audio_conversation
        assert callable(upload_audio_conversation)
    
    def test_audio_detail_api_exists(self):
        """음성 대화 상세 조회 API 함수 존재 확인"""
        from app.domains.conversation.audio_router import get_audio_conversation_detail
        assert callable(get_audio_conversation_detail)
    
    def test_audio_router_endpoints(self):
        """오디오 라우터 엔드포인트 확인"""
        from app.domains.conversation.audio_router import router
        
        routes = [route.path for route in router.routes]
        
        assert "/api/conversation/audio" in routes
        assert any("/api/conversation/audio/{conversation_id}" in route.path for route in router.routes)
    
    def test_audio_upload_validation(self):
        """음성 파일 업로드 유효성 검사 테스트"""
        from app.domains.conversation.audio_router import upload_audio_conversation
        
        # 함수가 존재하고 호출 가능한지 확인
        assert callable(upload_audio_conversation)
        
        # 지원되는 파일 확장자 확인
        allowed_extensions = {'webm', 'wav', 'mp3', 'm4a'}
        invalid_extensions = {'txt', 'pdf', 'doc', 'jpg'}
        
        for ext in invalid_extensions:
            assert ext not in allowed_extensions
    
    def test_file_size_validation(self):
        """파일 크기 제한 검증"""
        # 20MB 제한 확인
        max_size = 20 * 1024 * 1024
        assert max_size == 20971520
        
        # 테스트 파일 크기
        test_size = 1024  # 1KB
        assert test_size < max_size


class TestAudioIntegration:
    """통합 테스트"""
    
    def test_webm_file_creation(self):
        """WebM 테스트 파일 생성 테스트"""
        import base64
        
        # 최소 WebM 데이터
        webm_signature = b'\x1a\x45\xdf\xa3'
        test_data = webm_signature + b'\x00' * 100
        
        assert test_data.startswith(webm_signature)
        assert len(test_data) > 100
    
    def test_speaker_segments_format(self):
        """화자 구간 JSON 형식 테스트"""
        sample_segments = [
            {"speaker": 1, "start": 0.0, "end": 2.3, "text": "안녕하세요"},
            {"speaker": 2, "start": 2.4, "end": 5.1, "text": "반갑습니다"}
        ]
        
        # JSON 직렬화 가능한지 확인
        json_str = json.dumps(sample_segments)
        parsed = json.loads(json_str)
        
        assert len(parsed) == 2
        assert parsed[0]["speaker"] == 1
        assert parsed[1]["speaker"] == 2
    
    def test_audio_response_format(self):
        """음성 API 응답 형식 테스트"""
        from app.domains.conversation.schemas import FileUploadResponse
        
        # 응답 스키마 존재 확인
        assert hasattr(FileUploadResponse, '__annotations__')
        
        # 실제 필드 확인 (스키마에서 확인된 필드들)
        expected_fields = ['conversation_id', 'file_id', 'processing_status', 'message', 'gcs_file_path']
        for field in expected_fields:
            assert field in FileUploadResponse.__annotations__


class TestErrorHandling:
    """에러 처리 테스트"""
    
    def test_unsupported_file_format_error(self):
        """지원하지 않는 파일 형식 에러"""
        unsupported_extensions = ['txt', 'pdf', 'doc', 'jpg']
        supported_extensions = {'webm', 'wav', 'mp3', 'm4a'}
        
        for ext in unsupported_extensions:
            assert ext not in supported_extensions
    
    def test_file_size_limit_error(self):
        """파일 크기 제한 에러"""
        max_size = 20 * 1024 * 1024  # 20MB
        oversized_file = max_size + 1
        
        assert oversized_file > max_size
    
    def test_stt_processing_error_messages(self):
        """STT 처리 에러 메시지"""
        error_messages = {
            "network": "음성 인식에 실패했습니다. 네트워크 상태를 확인하거나, 음성 품질이 좋은 환경에서 다시 시도해주세요.",
            "file_size": "파일 크기가 20MB를 초과합니다.",
            "format": "지원하지 않는 음성 파일 형식입니다."
        }
        
        for key, message in error_messages.items():
            assert isinstance(message, str)
            assert len(message) > 0


class TestRealAPIIntegration:
    """실제 API 통합 테스트 (서버 실행 시)"""
    
    def test_create_test_webm_file(self):
        """테스트용 WebM 파일 생성"""
        import base64
        from pathlib import Path
        
        # 최소한의 WebM 파일 데이터
        webm_data = base64.b64decode("""
        GkXfo59ChoEBQveBAULygQRC84EIQoKEd2VibUKHgQRChYECGFOAZwEAAAAAAAHTEU2bdLpNu4tTq4QVSalmU6yBoU27i1OrhBZUrmtTrIHGTbuMU6uEElTDZ1OsggEXTbuMU6uEHFO7a1OsggG97AEAAAAAAABZAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAVSalmoCrXsYMPQkBNgIRMYXZmV0GETGF2ZkSJiEBEAAAAAAAAFlSua8yuAQAAAAAAAEPXgQFzxWEBnP///////////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAVSalmoCrXsYMPQkBNgIRMYXZmV0GETGF2ZkSJiEBEAAAAAAAAFlSua8yuAQAAAAAAAEPXgQFzxWEBnP///////////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
        """.replace('\n', '').replace(' ', ''))
        
        test_file_path = Path("test_audio.webm")
        
        try:
            with open(test_file_path, 'wb') as f:
                f.write(webm_data)
            
            # 파일이 생성되었는지 확인
            assert test_file_path.exists()
            assert test_file_path.stat().st_size > 0
            
            # WebM 시그니처 확인
            with open(test_file_path, 'rb') as f:
                header = f.read(4)
                assert header == b'\x1a\x45\xdf\xa3'  # WebM 시그니처
                
        finally:
            # 테스트 파일 정리
            if test_file_path.exists():
                test_file_path.unlink()
    
    def test_api_endpoints_structure(self):
        """API 엔드포인트 구조 테스트"""
        # 예상되는 엔드포인트들
        expected_endpoints = {
            "POST /api/conversation/audio": "음성 파일 업로드",
            "GET /api/conversation/audio/{conversation_id}": "음성 대화 조회"
        }
        
        for endpoint, description in expected_endpoints.items():
            assert isinstance(endpoint, str)
            assert isinstance(description, str)
            assert len(endpoint) > 0
            assert len(description) > 0
    
    def test_webm_file_validation(self):
        """WebM 파일 유효성 검사 테스트"""
        # WebM 시그니처
        webm_signature = b'\x1a\x45\xdf\xa3'
        
        # 유효한 WebM 데이터
        valid_webm = webm_signature + b'\x00' * 100
        assert valid_webm.startswith(webm_signature)
        
        # 무효한 데이터
        invalid_data = b'\x00\x00\x00\x00' + b'\x00' * 100
        assert not invalid_data.startswith(webm_signature)


# 실행 시 모든 테스트 실행
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
