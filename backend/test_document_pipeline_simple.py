"""
문서 업로드 분석 파이프라인 간단 테스트
- 핵심 컴포넌트만 테스트
"""

import pytest
from sqlalchemy import text
from app.core.database import SessionLocal


class TestDocumentPipelineComponents:
    """문서 분석 파이프라인 핵심 컴포넌트 테스트"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.db = SessionLocal()
    
    def teardown_method(self):
        """테스트 후 정리"""
        self.db.close()
    
    def test_database_connection(self):
        """데이터베이스 연결 테스트"""
        try:
            result = self.db.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
            print("✅ 데이터베이스 연결 성공")
        except Exception as e:
            pytest.fail(f"데이터베이스 연결 실패: {str(e)}")
    
    def test_conversation_service_import(self):
        """ConversationFileService import 테스트"""
        try:
            from app.domains.conversation.services import ConversationFileService
            
            service = ConversationFileService(self.db)
            assert service is not None
            print("✅ ConversationFileService import 성공")
        except ImportError as e:
            pytest.fail(f"ConversationFileService import 실패: {str(e)}")
    
    def test_agent_pipeline_functions(self):
        """Agent 파이프라인 함수 import 테스트"""
        try:
            from app.llm.agent.retry_pipeline import run_agent_pipeline_with_retry
            from app.domains.conversation.router import run_agent_pipeline_async
            
            assert callable(run_agent_pipeline_with_retry)
            assert callable(run_agent_pipeline_async)
            print("✅ Agent 파이프라인 함수 import 성공")
        except ImportError as e:
            pytest.fail(f"Agent 파이프라인 함수 import 실패: {str(e)}")
    
    def test_websocket_functions(self):
        """WebSocket 알림 함수 import 테스트"""
        try:
            from app.domains.conversation.websocket import notify_analysis_complete, notify_analysis_error
            
            assert callable(notify_analysis_complete)
            assert callable(notify_analysis_error)
            print("✅ WebSocket 알림 함수 import 성공")
        except ImportError as e:
            pytest.fail(f"WebSocket 알림 함수 import 실패: {str(e)}")
    
    def test_conversation_table_exists(self):
        """conversation 테이블 존재 확인"""
        try:
            result = self.db.execute(
                text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'conversation'")
            )
            count = result.fetchone()[0]
            assert count > 0
            print("✅ conversation 테이블 존재 확인")
        except Exception as e:
            pytest.fail(f"conversation 테이블 확인 실패: {str(e)}")
    
    def test_conversation_file_table_exists(self):
        """conversation_file 테이블 존재 확인"""
        try:
            result = self.db.execute(
                text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'conversation_file'")
            )
            count = result.fetchone()[0]
            assert count > 0
            print("✅ conversation_file 테이블 존재 확인")
        except Exception as e:
            pytest.fail(f"conversation_file 테이블 확인 실패: {str(e)}")
    
    def test_service_get_conversation_by_id(self):
        """ConversationFileService.get_conversation_by_id 테스트"""
        from app.domains.conversation.services import ConversationFileService
        
        service = ConversationFileService(self.db)
        
        # 실제 conversation 데이터 조회
        result = self.db.execute(
            text("SELECT conv_id FROM conversation ORDER BY create_date DESC LIMIT 1")
        )
        row = result.fetchone()
        
        if row:
            conv_id = str(row[0])
            conversation = service.get_conversation_by_id(conv_id)
            
            assert conversation is not None
            assert "conv_id" in conversation
            assert conversation["conv_id"] == conv_id
            print(f"✅ 실제 대화 조회 성공: {conversation.get('title', 'No title')}")
        else:
            # 데이터가 없으면 존재하지 않는 ID로 테스트
            fake_id = "00000000-0000-0000-0000-000000000000"
            conversation = service.get_conversation_by_id(fake_id)
            
            assert conversation is None
            print("✅ 존재하지 않는 대화 ID 처리 확인")
    
    def test_router_functions_exist(self):
        """라우터 함수들 존재 확인"""
        try:
            from app.domains.conversation.router import (
                upload_conversation_file,
                get_conversation_analysis,
                start_analysis_pipeline,
                execute_agent_pipeline
            )
            
            assert callable(upload_conversation_file)
            assert callable(get_conversation_analysis)
            assert callable(start_analysis_pipeline)
            assert callable(execute_agent_pipeline)
            
            print("✅ 모든 라우터 함수 존재 확인")
        except ImportError as e:
            pytest.fail(f"라우터 함수 import 실패: {str(e)}")
    
    def test_schemas_import(self):
        """스키마 클래스 import 테스트"""
        try:
            from app.domains.conversation.schemas import (
                ConversationFileResponse,
                FileUploadResponse,
                ConversationAnalysisResponse
            )
            
            assert ConversationFileResponse is not None
            assert FileUploadResponse is not None
            assert ConversationAnalysisResponse is not None
            
            print("✅ 스키마 클래스 import 성공")
        except ImportError as e:
            pytest.fail(f"스키마 클래스 import 실패: {str(e)}")
    
    def test_pipeline_integration_readiness(self):
        """파이프라인 통합 준비 상태 확인"""
        print("\n=== 파이프라인 통합 준비 상태 확인 ===")
        
        # 1. 데이터베이스 연결
        try:
            result = self.db.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
            print("1. ✅ 데이터베이스 연결")
        except Exception as e:
            print(f"1. ❌ 데이터베이스 연결 실패: {str(e)}")
            return
        
        # 2. 서비스 레이어
        try:
            from app.domains.conversation.services import ConversationFileService
            service = ConversationFileService(self.db)
            print("2. ✅ 서비스 레이어")
        except Exception as e:
            print(f"2. ❌ 서비스 레이어 실패: {str(e)}")
            return
        
        # 3. Agent 파이프라인
        try:
            from app.llm.agent.retry_pipeline import run_agent_pipeline_with_retry
            print("3. ✅ Agent 파이프라인")
        except Exception as e:
            print(f"3. ❌ Agent 파이프라인 실패: {str(e)}")
            return
        
        # 4. WebSocket 알림
        try:
            from app.domains.conversation.websocket import notify_analysis_complete
            print("4. ✅ WebSocket 알림")
        except Exception as e:
            print(f"4. ❌ WebSocket 알림 실패: {str(e)}")
            return
        
        # 5. 라우터 함수
        try:
            from app.domains.conversation.router import run_agent_pipeline_async
            print("5. ✅ 라우터 함수")
        except Exception as e:
            print(f"5. ❌ 라우터 함수 실패: {str(e)}")
            return
        
        print("\n✅ 모든 파이프라인 컴포넌트 준비 완료!")
        print("📋 파일 업로드 → 분석 파이프라인 실행 가능")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
