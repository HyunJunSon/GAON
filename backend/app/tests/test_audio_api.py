import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import io
import json

from app.main import app
from app.domains.conversation.models import Conversation
from app.domains.conversation.file_models import ConversationFile
from app.domains.auth.user_models import User


client = TestClient(app)


@pytest.fixture
def mock_user():
    """테스트용 사용자 객체"""
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    return user


@pytest.fixture
def mock_db_session():
    """테스트용 DB 세션"""
    return Mock()


@pytest.fixture
def sample_audio_file():
    """테스트용 오디오 파일 데이터"""
    # WebM 파일 시그니처 (간단한 더미 데이터)
    webm_header = b'\x1a\x45\xdf\xa3'  # WebM 시그니처
    return webm_header + b'dummy_audio_data' * 100


@pytest.fixture
def mock_stt_result():
    """STT 처리 결과 Mock"""
    return {
        "transcript": "안녕하세요. 반갑습니다.",
        "speaker_segments": [
            {"speaker": 1, "start": 0.0, "end": 2.3, "text": "안녕하세요"},
            {"speaker": 2, "start": 2.4, "end": 5.1, "text": "반갑습니다"}
        ],
        "duration": 5,
        "speaker_count": 2
    }


class TestAudioUploadAPI:
    """Task 1-3: 음성 업로드 API 테스트"""
    
    @patch('app.domains.conversation.audio_router.get_current_user')
    @patch('app.domains.conversation.audio_router.get_db')
    @patch('app.domains.conversation.audio_router.STTService')
    @patch('app.domains.conversation.audio_router.ConversationFileService')
    def test_upload_audio_success(self, mock_file_service, mock_stt_service, 
                                 mock_get_db, mock_get_current_user, 
                                 mock_user, mock_db_session, sample_audio_file, mock_stt_result):
        """음성 파일 업로드 성공 테스트"""
        # Mock 설정
        mock_get_current_user.return_value = mock_user
        mock_get_db.return_value = mock_db_session
        
        # STT 서비스 Mock
        mock_stt_instance = Mock()
        mock_stt_instance.validate_audio_format.return_value = True
        mock_stt_instance.transcribe_audio_with_diarization.return_value = mock_stt_result
        mock_stt_service.return_value = mock_stt_instance
        
        # 파일 서비스 Mock
        mock_file_service_instance = Mock()
        mock_file_service_instance.file_processor.upload_to_gcs.return_value = "gcs://bucket/audio.webm"
        mock_file_service.return_value = mock_file_service_instance
        
        # DB Mock 설정
        mock_conversation = Mock()
        mock_conversation.id = 1
        mock_conversation.participants = []
        
        mock_db_file = Mock()
        mock_db_file.id = 1
        
        mock_db_session.add = Mock()
        mock_db_session.flush = Mock()
        mock_db_session.commit = Mock()
        
        # 테스트 실행
        files = {"file": ("test_audio.webm", io.BytesIO(sample_audio_file), "audio/webm")}
        data = {"family_id": "1"}
        
        response = client.post("/api/conversation/audio", files=files, data=data)
        
        # 검증
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "completed"
        assert "성공적으로 업로드" in response_data["message"]
        
        # STT 서비스 호출 확인
        mock_stt_instance.transcribe_audio_with_diarization.assert_called_once()
        
        # DB 저장 확인
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called_once()
    
    @patch('app.domains.conversation.audio_router.get_current_user')
    @patch('app.domains.conversation.audio_router.get_db')
    def test_upload_audio_invalid_format(self, mock_get_db, mock_get_current_user, mock_user):
        """잘못된 파일 형식 업로드 테스트"""
        mock_get_current_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        
        # 잘못된 형식 파일
        files = {"file": ("test.txt", io.BytesIO(b"text content"), "text/plain")}
        data = {"family_id": "1"}
        
        response = client.post("/api/conversation/audio", files=files, data=data)
        
        assert response.status_code == 400
        assert "지원하지 않는 음성 파일 형식" in response.json()["detail"]
    

    def test_upload_audio_file_too_large(self, mock_get_db, mock_get_current_user, mock_user):
        """파일 크기 초과 테스트"""
        mock_get_current_user.return_value = mock_user
        mock_get_db.return_value = Mock()
        
        # 20MB 초과 파일 (21MB)
        large_file_content = b'x' * (21 * 1024 * 1024)
        files = {"file": ("large_audio.webm", io.BytesIO(large_file_content), "audio/webm")}
        data = {"family_id": "1"}
        
        response = client.post("/api/conversation/audio", files=files, data=data)
        
        assert response.status_code == 400
        assert "파일 크기가 너무 큽니다" in response.json()["detail"]


class TestAudioDetailAPI:
    """Task 1-4: 음성 대화 조회 API 테스트"""
    
    @patch('app.domains.conversation.audio_router.get_current_user')
    @patch('app.domains.conversation.audio_router.get_db')
    def test_get_audio_conversation_detail_success(self, mock_get_db, mock_get_current_user, mock_user):
        """음성 대화 상세 조회 성공 테스트"""
        # Mock 설정
        mock_get_current_user.return_value = mock_user
        mock_db_session = Mock()
        mock_get_db.return_value = mock_db_session
        
        # Conversation Mock
        mock_conversation = Mock()
        mock_conversation.id = 1
        mock_conversation.title = "음성 대화 - test.webm"
        mock_conversation.create_date = "2024-01-01T00:00:00"
        mock_conversation.family_id = 1
        mock_conversation.participants = [mock_user]
        
        # ConversationFile Mock
        mock_audio_file = Mock()
        mock_audio_file.id = 1
        mock_audio_file.original_filename = "test.webm"
        mock_audio_file.file_size = 1024
        mock_audio_file.duration = 60
        mock_audio_file.speaker_count = 2
        mock_audio_file.audio_url = "gcs://bucket/audio.webm"
        mock_audio_file.processing_status = "completed"
        mock_audio_file.transcript = "안녕하세요. 반갑습니다."
        mock_audio_file.speaker_segments = [
            {"speaker": 1, "start": 0.0, "end": 2.3, "text": "안녕하세요"},
            {"speaker": 2, "start": 2.4, "end": 5.1, "text": "반갑습니다"}
        ]
        
        # DB 쿼리 Mock
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [
            mock_conversation,  # 첫 번째 쿼리 (Conversation)
            mock_audio_file     # 두 번째 쿼리 (ConversationFile)
        ]
        
        # 테스트 실행
        response = client.get("/api/conversation/audio/1")
        
        # 검증
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["conversation_id"] == 1
        assert response_data["title"] == "음성 대화 - test.webm"
        assert response_data["file_info"]["duration"] == 60
        assert response_data["file_info"]["speaker_count"] == 2
        assert response_data["transcript"]["full_text"] == "안녕하세요. 반갑습니다."
        assert len(response_data["transcript"]["speaker_segments"]) == 2
    
    @patch('app.domains.conversation.audio_router.get_current_user')
    @patch('app.domains.conversation.audio_router.get_db')
    def test_get_audio_conversation_not_found(self, mock_get_db, mock_get_current_user, mock_user):
        """존재하지 않는 대화 조회 테스트"""
        mock_get_current_user.return_value = mock_user
        mock_db_session = Mock()
        mock_get_db.return_value = mock_db_session
        
        # 대화를 찾을 수 없음
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/api/conversation/audio/999")
        
        assert response.status_code == 404
        assert "대화를 찾을 수 없습니다" in response.json()["detail"]
    
    @patch('app.domains.conversation.audio_router.get_current_user')
    @patch('app.domains.conversation.audio_router.get_db')
    def test_get_audio_conversation_access_denied(self, mock_get_db, mock_get_current_user, mock_user):
        """권한 없는 대화 조회 테스트"""
        mock_get_current_user.return_value = mock_user
        mock_db_session = Mock()
        mock_get_db.return_value = mock_db_session
        
        # 다른 사용자의 대화
        other_user = Mock()
        other_user.id = 2
        
        mock_conversation = Mock()
        mock_conversation.participants = [other_user]  # 현재 사용자가 참여자가 아님
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_conversation
        
        response = client.get("/api/conversation/audio/1")
        
        assert response.status_code == 403
        assert "접근할 권한이 없습니다" in response.json()["detail"]
