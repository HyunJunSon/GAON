import pytest
from unittest.mock import Mock, patch, MagicMock
from app.domains.conversation.stt_service import STTService


class TestSTTService:
    """STTService 클래스 테스트"""
    
    @patch('app.domains.conversation.stt_service.speech.SpeechClient')
    def test_stt_service_initialization(self, mock_speech_client):
        """STTService 초기화 테스트"""
        # Mock 설정
        mock_client = Mock()
        mock_speech_client.return_value = mock_client
        
        # STTService 초기화
        stt_service = STTService()
        
        # 검증
        assert stt_service.client == mock_client
        mock_speech_client.assert_called_once()
    
    @patch('app.domains.conversation.stt_service.speech.SpeechClient')
    def test_stt_service_initialization_failure(self, mock_speech_client):
        """STTService 초기화 실패 테스트"""
        # Mock에서 예외 발생 설정
        mock_speech_client.side_effect = Exception("API 키 오류")
        
        # 예외 발생 확인
        with pytest.raises(Exception) as exc_info:
            STTService()
        
        assert "API 키 오류" in str(exc_info.value)
    
    @patch('app.domains.conversation.stt_service.speech.SpeechClient')
    def test_transcribe_audio_with_diarization_success(self, mock_speech_client):
        """음성 인식 및 화자 구분 성공 테스트"""
        # Mock 설정
        mock_client = Mock()
        mock_speech_client.return_value = mock_client
        
        # Mock 응답 데이터 생성
        mock_word1 = Mock()
        mock_word1.word = "안녕하세요"
        mock_word1.speaker_tag = 1
        mock_word1.start_time.total_seconds.return_value = 0.0
        mock_word1.end_time.total_seconds.return_value = 1.0
        
        mock_word2 = Mock()
        mock_word2.word = "반갑습니다"
        mock_word2.speaker_tag = 2
        mock_word2.start_time.total_seconds.return_value = 1.5
        mock_word2.end_time.total_seconds.return_value = 2.5
        
        mock_alternative = Mock()
        mock_alternative.transcript = "안녕하세요 반갑습니다"
        mock_alternative.words = [mock_word1, mock_word2]
        
        mock_result = Mock()
        mock_result.alternatives = [mock_alternative]
        
        mock_response = Mock()
        mock_response.results = [mock_result]
        
        mock_client.recognize.return_value = mock_response
        
        # STTService 생성 및 테스트
        stt_service = STTService()
        audio_content = b"fake_audio_data"
        
        result = stt_service.transcribe_audio_with_diarization(audio_content)
        
        # 결과 검증
        assert result["transcript"] == "안녕하세요 반갑습니다"
        assert result["speaker_count"] == 2
        assert len(result["speaker_segments"]) >= 1
        assert result["duration"] >= 0
    
    @patch('app.domains.conversation.stt_service.speech.SpeechClient')
    def test_transcribe_audio_empty_response(self, mock_speech_client):
        """빈 응답 처리 테스트"""
        # Mock 설정
        mock_client = Mock()
        mock_speech_client.return_value = mock_client
        
        # 빈 응답 설정
        mock_response = Mock()
        mock_response.results = []
        mock_client.recognize.return_value = mock_response
        
        # STTService 생성 및 테스트
        stt_service = STTService()
        audio_content = b"fake_audio_data"
        
        result = stt_service.transcribe_audio_with_diarization(audio_content)
        
        # 빈 결과 검증
        assert result["transcript"] == ""
        assert result["speaker_segments"] == []
        assert result["duration"] == 0
        assert result["speaker_count"] == 0
    
    @patch('app.domains.conversation.stt_service.speech.SpeechClient')
    def test_transcribe_audio_api_error(self, mock_speech_client):
        """STT API 오류 처리 테스트"""
        # Mock 설정
        mock_client = Mock()
        mock_speech_client.return_value = mock_client
        
        # API 오류 설정
        mock_client.recognize.side_effect = Exception("API 호출 실패")
        
        # STTService 생성 및 테스트
        stt_service = STTService()
        audio_content = b"fake_audio_data"
        
        # 예외 발생 확인
        with pytest.raises(Exception) as exc_info:
            stt_service.transcribe_audio_with_diarization(audio_content)
        
        assert "음성 인식 처리 중 오류가 발생했습니다" in str(exc_info.value)
    
    def test_validate_audio_format_webm(self):
        """WebM 오디오 형식 검증 테스트"""
        stt_service = STTService.__new__(STTService)  # __init__ 호출 없이 인스턴스 생성
        
        # WebM 시그니처가 있는 가짜 데이터
        webm_audio = b'\x1a\x45\xdf\xa3' + b'fake_webm_data'
        
        result = stt_service.validate_audio_format(webm_audio)
        assert result is True
    
    def test_validate_audio_format_invalid(self):
        """잘못된 오디오 형식 검증 테스트"""
        stt_service = STTService.__new__(STTService)  # __init__ 호출 없이 인스턴스 생성
        
        # 잘못된 시그니처
        invalid_audio = b'invalid_audio_data'
        
        result = stt_service.validate_audio_format(invalid_audio)
        assert result is False
    
    def test_validate_audio_format_too_short(self):
        """너무 짧은 오디오 데이터 검증 테스트"""
        stt_service = STTService.__new__(STTService)  # __init__ 호출 없이 인스턴스 생성
        
        # 4바이트 미만의 데이터
        short_audio = b'abc'
        
        result = stt_service.validate_audio_format(short_audio)
        assert result is False
    
    def test_parse_recognition_response_structure(self):
        """STT 응답 파싱 결과 구조 테스트"""
        stt_service = STTService.__new__(STTService)  # __init__ 호출 없이 인스턴스 생성
        
        # Mock 응답 생성 (더 정확한 Mock 설정)
        mock_word = Mock()
        mock_word.word = "테스트"
        mock_word.speaker_tag = 1
        mock_word.start_time.total_seconds.return_value = 0.0
        mock_word.end_time.total_seconds.return_value = 1.0
        
        mock_alternative = Mock()
        mock_alternative.transcript = "테스트 문장"
        mock_alternative.words = [mock_word]
        
        mock_result = Mock()
        mock_result.alternatives = [mock_alternative]
        
        mock_response = Mock()
        mock_response.results = [mock_result]
        
        # 파싱 실행
        result = stt_service._parse_recognition_response(mock_response)
        
        # 결과 구조 검증
        assert "transcript" in result
        assert "speaker_segments" in result
        assert "duration" in result
        assert "speaker_count" in result
        
        assert isinstance(result["transcript"], str)
        assert isinstance(result["speaker_segments"], list)
        assert isinstance(result["duration"], int)
        assert isinstance(result["speaker_count"], int)
        
        # 실제 값 검증
        assert result["transcript"] == "테스트 문장"
        assert result["speaker_count"] == 1
        assert len(result["speaker_segments"]) == 1
        assert result["speaker_segments"][0]["speaker"] == 1
        assert result["speaker_segments"][0]["text"] == "테스트"
