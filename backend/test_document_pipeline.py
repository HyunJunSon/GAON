"""
문서 업로드 분석 파이프라인 통합 테스트
- 파일 업로드부터 분석 완료까지 전체 플로우 테스트
"""

import pytest
import asyncio
import tempfile
import os
from io import BytesIO
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.core.database import SessionLocal
from app.domains.conversation.services import ConversationFileService


class TestDocumentAnalysisPipeline:
    """문서 업로드 분석 파이프라인 테스트"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.client = TestClient(app)
        self.db = SessionLocal()
        self.test_user_token = None
    
    def teardown_method(self):
        """테스트 후 정리"""
        self.db.close()
    
    def get_test_token(self):
        """테스트용 토큰 생성"""
        if self.test_user_token:
            return self.test_user_token
            
        # 테스트 사용자 로그인
        login_data = {
            "username": "test@example.com",
            "password": "testpassword"
        }
        
        response = self.client.post("/api/auth/login", data=login_data)
        if response.status_code == 200:
            self.test_user_token = response.json()["access_token"]
            return self.test_user_token
        
        # 사용자가 없으면 생성
        register_data = {
            "email": "test@example.com",
            "password": "testpassword",
            "name": "테스트사용자"
        }
        
        register_response = self.client.post("/api/auth/register", json=register_data)
        if register_response.status_code == 201:
            login_response = self.client.post("/api/auth/login", data=login_data)
            if login_response.status_code == 200:
                self.test_user_token = login_response.json()["access_token"]
                return self.test_user_token
        
        return None
    
    def create_test_audio_file(self):
        """테스트용 오디오 파일 생성"""
        # 간단한 WAV 파일 헤더 생성
        wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
        audio_data = b'\x00' * 2048  # 2KB의 더미 오디오 데이터
        
        return BytesIO(wav_header + audio_data)
    
    def test_file_upload_endpoint(self):
        """파일 업로드 엔드포인트 테스트"""
        token = self.get_test_token()
        if not token:
            pytest.skip("테스트 사용자 토큰을 얻을 수 없습니다")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 테스트 파일 생성
        test_file = self.create_test_audio_file()
        
        files = {"file": ("test_audio.wav", test_file, "audio/wav")}
        data = {"family_id": 1}
        
        response = self.client.post(
            "/api/conversations/analyze",
            headers=headers,
            files=files,
            data=data
        )
        
        print(f"업로드 응답 상태: {response.status_code}")
        print(f"업로드 응답 내용: {response.json()}")
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert "conversation_id" in response_data
        assert "file_id" in response_data
        assert "status" in response_data
        
        print(f"✅ 파일 업로드 성공: conversation_id={response_data['conversation_id']}")
        return response_data
    
    def test_conversation_creation(self):
        """대화 생성 확인"""
        upload_result = self.test_file_upload_endpoint()
        conversation_id = upload_result["conversation_id"]
        
        # 데이터베이스에서 대화 확인
        result = self.db.execute(
            text("SELECT * FROM conversation WHERE conv_id = :conv_id"),
            {"conv_id": conversation_id}
        )
        conversation = result.fetchone()
        
        assert conversation is not None
        print(f"✅ 대화 생성 확인: {conversation.title}")
    
    def test_file_processing_status(self):
        """파일 처리 상태 확인"""
        upload_result = self.test_file_upload_endpoint()
        file_id = upload_result["file_id"]
        
        token = self.get_test_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # 파일 정보 조회
        response = self.client.get(
            f"/api/conversations/files/{file_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        file_data = response.json()
        
        assert "processing_status" in file_data
        assert "gcs_file_path" in file_data
        
        print(f"✅ 파일 처리 상태: {file_data['processing_status']}")
    
    def test_analysis_pipeline_start(self):
        """분석 파이프라인 시작 테스트"""
        upload_result = self.test_file_upload_endpoint()
        conversation_id = upload_result["conversation_id"]
        
        token = self.get_test_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # 분석 시작
        response = self.client.post(
            f"/api/analysis/{conversation_id}/start",
            headers=headers
        )
        
        print(f"분석 시작 응답: {response.status_code}, {response.json()}")
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["status"] == "started"
        assert response_data["conversation_id"] == conversation_id
        
        print(f"✅ 분석 파이프라인 시작 성공")
    
    def test_service_layer_functions(self):
        """서비스 레이어 함수 테스트"""
        service = ConversationFileService(self.db)
        
        # 최근 대화 조회
        result = self.db.execute(
            text("SELECT conv_id FROM conversation ORDER BY create_date DESC LIMIT 1")
        )
        row = result.fetchone()
        
        if row:
            conv_id = str(row[0])
            conversation = service.get_conversation_by_id(conv_id)
            
            assert conversation is not None
            assert "conv_id" in conversation
            print(f"✅ 서비스 레이어 대화 조회 성공")
        else:
            print("⚠️ 테스트할 대화 데이터가 없습니다")
    
    def test_agent_pipeline_import(self):
        """Agent 파이프라인 import 테스트"""
        try:
            from app.llm.agent.retry_pipeline import run_agent_pipeline_with_retry
            from app.domains.conversation.router import run_agent_pipeline_async
            
            assert callable(run_agent_pipeline_with_retry)
            assert callable(run_agent_pipeline_async)
            
            print("✅ Agent 파이프라인 함수 import 성공")
        except ImportError as e:
            pytest.fail(f"Agent 파이프라인 import 실패: {str(e)}")
    
    def test_websocket_notification_import(self):
        """WebSocket 알림 함수 import 테스트"""
        try:
            from app.domains.conversation.websocket import notify_analysis_complete, notify_analysis_error
            
            assert callable(notify_analysis_complete)
            assert callable(notify_analysis_error)
            
            print("✅ WebSocket 알림 함수 import 성공")
        except ImportError as e:
            pytest.fail(f"WebSocket 알림 함수 import 실패: {str(e)}")
    
    def test_full_pipeline_integration(self):
        """전체 파이프라인 통합 테스트"""
        print("\n=== 전체 파이프라인 통합 테스트 시작 ===")
        
        # 1. 파일 업로드
        upload_result = self.test_file_upload_endpoint()
        conversation_id = upload_result["conversation_id"]
        file_id = upload_result["file_id"]
        
        print(f"1. 파일 업로드 완료: conversation_id={conversation_id}")
        
        # 2. 대화 생성 확인
        service = ConversationFileService(self.db)
        conversation = service.get_conversation_by_id(conversation_id)
        assert conversation is not None
        print(f"2. 대화 생성 확인: {conversation['title']}")
        
        # 3. 파일 정보 확인
        file_info = service.get_file_by_id(file_id)
        assert file_info is not None
        print(f"3. 파일 정보 확인: {file_info.processing_status}")
        
        # 4. 분석 파이프라인 시작
        token = self.get_test_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.client.post(
            f"/api/analysis/{conversation_id}/start",
            headers=headers
        )
        assert response.status_code == 200
        print("4. 분석 파이프라인 시작 완료")
        
        print("✅ 전체 파이프라인 통합 테스트 성공")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
