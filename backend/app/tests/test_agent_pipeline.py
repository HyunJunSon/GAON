"""
Agent 파이프라인 통합 테스트
- Cleaner → Analysis → QA 전체 플로우 검증
- 실제 DB 및 LLM API 사용
"""

import pytest
import os
from app.llm.agent.main_run import main as run_agent_pipeline
from app.core.database import SessionLocal
from sqlalchemy import text


class TestAgentPipeline:
    """Agent 파이프라인 통합 테스트"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.db = SessionLocal()
        # 테스트 환경 활성화
        os.environ["USE_TEST_DB"] = "true"
    
    def teardown_method(self):
        """테스트 후 정리"""
        self.db.close()
    
    def test_agent_pipeline_execution(self):
        """Agent 파이프라인 전체 실행 테스트"""
        
        # 최근 conversation 데이터 확인
        result = self.db.execute(
            text("SELECT conv_id, id FROM conversation ORDER BY create_date DESC LIMIT 1")
        )
        row = result.fetchone()
        
        if not row:
            pytest.skip("테스트할 conversation 데이터가 없습니다")
        
        conv_id, user_id = str(row[0]), row[1]
        print(f"테스트 대상: conv_id={conv_id}, user_id={user_id}")
        
        # Agent 파이프라인 실행
        try:
            pipeline_result = run_agent_pipeline()
            
            # 결과 검증
            assert pipeline_result is not None
            assert "conv_id" in pipeline_result
            assert "analysis_id" in pipeline_result
            assert "status" in pipeline_result
            assert pipeline_result["status"] == "completed"
            
            print(f"✅ 파이프라인 실행 성공: {pipeline_result}")
            
        except Exception as e:
            pytest.fail(f"Agent 파이프라인 실행 실패: {str(e)}")
    
    def test_cleaner_module_import(self):
        """Cleaner 모듈 import 테스트"""
        try:
            from app.llm.agent.Cleaner.run_cleaner import run_cleaner
            assert callable(run_cleaner)
        except ImportError as e:
            pytest.fail(f"Cleaner 모듈 import 실패: {str(e)}")
    
    def test_analysis_module_import(self):
        """Analysis 모듈 import 테스트"""
        try:
            from app.llm.agent.Analysis.run_analysis import run_analysis
            assert callable(run_analysis)
        except ImportError as e:
            pytest.fail(f"Analysis 모듈 import 실패: {str(e)}")
    
    def test_qa_module_import(self):
        """QA 모듈 import 테스트"""
        try:
            from app.llm.agent.QA.run_qa import run_qa
            assert callable(run_qa)
        except ImportError as e:
            pytest.fail(f"QA 모듈 import 실패: {str(e)}")
    
    def test_crud_functions(self):
        """CRUD 함수 테스트"""
        try:
            from app.llm.agent.crud import (
                get_conversation_by_id,
                get_user_by_id,
                save_analysis_result
            )
            
            assert callable(get_conversation_by_id)
            assert callable(get_user_by_id)
            assert callable(save_analysis_result)
            
        except ImportError as e:
            pytest.fail(f"CRUD 함수 import 실패: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
