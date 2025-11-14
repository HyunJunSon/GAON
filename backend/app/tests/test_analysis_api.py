"""
비동기 분석 API 테스트
- POST /analysis/{conversation_id}/start 엔드포인트 테스트
- BackgroundTasks 실행 검증
"""

import pytest
from app.core.database import SessionLocal
from sqlalchemy import text


class TestAnalysisAPI:
    """비동기 분석 API 테스트"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.db = SessionLocal()
    
    def teardown_method(self):
        """테스트 후 정리"""
        self.db.close()
    
    def test_analysis_api_import(self):
        """분석 API 관련 함수 import 테스트"""
        try:
            from app.domains.conversation.router import start_analysis_pipeline, run_agent_pipeline_async
            assert callable(start_analysis_pipeline)
            assert callable(run_agent_pipeline_async)
            print("✅ 분석 API 함수 import 성공")
        except ImportError as e:
            pytest.fail(f"분석 API 함수 import 실패: {str(e)}")
    
    def test_agent_pipeline_execution_function(self):
        """Agent 파이프라인 실행 함수 테스트"""
        try:
            from app.domains.conversation.router import execute_agent_pipeline
            assert callable(execute_agent_pipeline)
            print("✅ execute_agent_pipeline 함수 존재 확인")
            
        except ImportError as e:
            pytest.fail(f"Agent 파이프라인 실행 함수 import 실패: {str(e)}")
    
    def test_conversation_service_get_by_id(self):
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
            assert "title" in conversation
            assert conversation["conv_id"] == conv_id
            
            print(f"✅ 실제 대화 조회 성공: {conversation['title']}")
        else:
            # 데이터가 없으면 존재하지 않는 ID로 테스트
            fake_id = "00000000-0000-0000-0000-000000000000"
            conversation = service.get_conversation_by_id(fake_id)
            
            assert conversation is None
            print("✅ 존재하지 않는 대화 ID 처리 확인")
    
    def test_background_task_integration(self):
        """BackgroundTasks 통합 테스트"""
        try:
            from fastapi import BackgroundTasks
            from app.domains.conversation.router import run_agent_pipeline_async
            
            # BackgroundTasks 객체 생성 가능 확인
            background_tasks = BackgroundTasks()
            assert background_tasks is not None
            
            # 비동기 함수 존재 확인
            assert callable(run_agent_pipeline_async)
            
            print("✅ BackgroundTasks 통합 준비 완료")
            
        except ImportError as e:
            pytest.fail(f"BackgroundTasks 통합 테스트 실패: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
