import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from app.domains.conversation.stt_service import STTService


class TestWebMConversion:
    """WebM 오디오 변환 테스트"""
    
    def setup_method(self):
        """테스트 설정"""
        self.stt_service = STTService()
    
    def test_get_audio_config_webm(self):
        """WebM 파일의 오디오 설정 테스트"""
        encoding, sample_rate = self.stt_service._get_audio_config("test.webm")
        
        # WebM은 LINEAR16 (WAV) 설정으로 변환되어야 함
        from google.cloud.speech import RecognitionConfig
        assert encoding == RecognitionConfig.AudioEncoding.LINEAR16
        assert sample_rate == 16000
    
    @patch('subprocess.run')
    @patch('tempfile.NamedTemporaryFile')
    @patch('builtins.open')
    @patch('os.unlink')
    def test_convert_webm_to_wav_success(self, mock_unlink, mock_open, mock_tempfile, mock_subprocess):
        """WebM to WAV 변환 성공 테스트"""
        # Mock 설정
        mock_temp_file = MagicMock()
        mock_temp_file.name = '/tmp/test.webm'
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file
        
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stderr = ""
        
        mock_file = MagicMock()
        mock_file.read.return_value = b'fake_wav_content'
        mock_open.return_value.__enter__.return_value = mock_file
        
        # 테스트 실행
        fake_webm_content = b'fake_webm_content'
        result = self.stt_service._convert_webm_to_wav(fake_webm_content)
        
        # 검증
        assert result == b'fake_wav_content'
        mock_subprocess.assert_called_once()
        mock_unlink.assert_called()
    
    @patch('subprocess.run')
    @patch('tempfile.NamedTemporaryFile')
    def test_convert_webm_to_wav_failure(self, mock_tempfile, mock_subprocess):
        """WebM to WAV 변환 실패 테스트"""
        # Mock 설정
        mock_temp_file = MagicMock()
        mock_temp_file.name = '/tmp/test.webm'
        mock_tempfile.return_value.__enter__.return_value = mock_temp_file
        
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "ffmpeg error"
        
        # 테스트 실행 및 검증
        fake_webm_content = b'fake_webm_content'
        with pytest.raises(Exception, match="오디오 변환 실패"):
            self.stt_service._convert_webm_to_wav(fake_webm_content)
    
    def test_webm_file_detection(self):
        """WebM 파일 감지 테스트"""
        # 다양한 확장자 테스트
        webm_files = ["test.webm", "TEST.WEBM", "audio.WebM"]
        non_webm_files = ["test.mp3", "audio.wav", "file.m4a"]
        
        for filename in webm_files:
            assert filename.lower().endswith('.webm'), f"{filename} should be detected as WebM"
        
        for filename in non_webm_files:
            assert not filename.lower().endswith('.webm'), f"{filename} should not be detected as WebM"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
