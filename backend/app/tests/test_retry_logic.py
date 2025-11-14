"""
재시도 로직 테스트
- Agent 단계별 재시도 메커니즘 검증
- 캐시 시스템 동작 확인
- 실패 시나리오 테스트
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.llm.agent.retry_pipeline import (
    RetryableAgentPipeline, 
    RetryConfig, 
    run_agent_pipeline_with_retry
)


class TestRetryLogic:
    """재시도 로직 테스트"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.config = RetryConfig(max_retries=2, base_delay=0.1)  # 빠른 테스트를 위해 지연 시간 단축
        self.pipeline = RetryableAgentPipeline(self.config)
    
    def test_retry_config_creation(self):
        """재시도 설정 생성 테스트"""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.base_delay == 2.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        
        print("✅ 재시도 설정 생성 확인")
    
    def test_cache_key_generation(self):
        """캐시 키 생성 테스트"""
        cache_key = self.pipeline._get_cache_key("cleaner", "test-conv-id")
        
        assert cache_key == "cleaner:test-conv-id"
        print("✅ 캐시 키 생성 확인")
    
    def test_cache_operations(self):
        """캐시 저장/조회 테스트"""
        step_name = "test_step"
        conv_id = "test-conv-id"
        test_result = {"status": "success", "data": "test"}
        
        # 캐시 저장
        self.pipeline._set_cached_result(step_name, conv_id, test_result)
        
        # 캐시 조회
        cached_result = self.pipeline._get_cached_result(step_name, conv_id)
        
        assert cached_result == test_result
        print("✅ 캐시 저장/조회 확인")
    
    @pytest.mark.asyncio
    async def test_successful_step_execution(self):
        """성공적인 단계 실행 테스트"""
        
        # Mock 함수 생성
        mock_func = MagicMock(return_value={"status": "success"})
        
        # 단계 실행
        result = await self.pipeline._execute_step_with_retry(
            "test_step", mock_func, "test-conv-id"
        )
        
        assert result.success is True
        assert result.step_name == "test_step"
        assert result.result == {"status": "success"}
        assert result.attempt == 1
        assert result.cached is False
        
        print("✅ 성공적인 단계 실행 확인")
    
    @pytest.mark.asyncio
    async def test_cached_result_usage(self):
        """캐시된 결과 사용 테스트"""
        
        # 캐시에 결과 미리 저장
        cached_data = {"status": "cached", "data": "from_cache"}
        self.pipeline._set_cached_result("test_step", "test-conv-id", cached_data)
        
        # Mock 함수 (호출되지 않아야 함)
        mock_func = MagicMock()
        
        # 단계 실행
        result = await self.pipeline._execute_step_with_retry(
            "test_step", mock_func, "test-conv-id"
        )
        
        assert result.success is True
        assert result.cached is True
        assert result.result == cached_data
        assert mock_func.call_count == 0  # 캐시 사용으로 함수 호출 안됨
        
        print("✅ 캐시된 결과 사용 확인")
    
    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """실패 시 재시도 테스트"""
        
        # 첫 번째 호출은 실패, 두 번째 호출은 성공하는 Mock
        mock_func = MagicMock(side_effect=[
            Exception("첫 번째 실패"),
            {"status": "success_after_retry"}
        ])
        
        # 단계 실행
        result = await self.pipeline._execute_step_with_retry(
            "test_step", mock_func, "test-conv-id"
        )
        
        assert result.success is True
        assert result.attempt == 2  # 두 번째 시도에서 성공
        assert result.result == {"status": "success_after_retry"}
        assert mock_func.call_count == 2
        
        print("✅ 실패 시 재시도 확인")
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """최대 재시도 횟수 초과 테스트"""
        
        # 항상 실패하는 Mock
        mock_func = MagicMock(side_effect=Exception("항상 실패"))
        
        # 단계 실행
        result = await self.pipeline._execute_step_with_retry(
            "test_step", mock_func, "test-conv-id"
        )
        
        assert result.success is False
        assert result.attempt == self.config.max_retries
        assert "항상 실패" in result.error
        assert mock_func.call_count == self.config.max_retries
        
        print("✅ 최대 재시도 횟수 초과 처리 확인")
    
    def test_retry_pipeline_import(self):
        """재시도 파이프라인 모듈 import 테스트"""
        try:
            from app.llm.agent.retry_pipeline import (
                RetryableAgentPipeline,
                RetryConfig,
                run_agent_pipeline_with_retry
            )
            
            assert callable(RetryableAgentPipeline)
            assert callable(run_agent_pipeline_with_retry)
            
            print("✅ 재시도 파이프라인 모듈 import 성공")
            
        except ImportError as e:
            pytest.fail(f"재시도 파이프라인 모듈 import 실패: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_pipeline_integration(self):
        """파이프라인 통합 테스트 (Mock 사용)"""
        
        with patch('app.llm.agent.retry_pipeline.run_cleaner') as mock_cleaner, \
             patch('app.llm.agent.retry_pipeline.run_analysis') as mock_analysis, \
             patch('app.llm.agent.retry_pipeline.run_qa') as mock_qa:
            
            # Mock 반환값 설정
            mock_cleaner.return_value = {
                "conv_id": "test-conv-id",
                "id": 1,
                "cleaned_df": "mock_df",
                "validated": True
            }
            
            mock_analysis.return_value = {
                "analysis_id": "test-analysis-id",
                "analysis_result": {"score": 85}
            }
            
            mock_qa.return_value = {
                "confidence": 0.9,
                "status": "completed"
            }
            
            # 파이프라인 실행
            result = await run_agent_pipeline_with_retry("test-conv-id")
            
            assert result["status"] == "completed"
            assert result["conv_id"] == "test-conv-id"
            assert result["score"] == 85
            assert result["confidence"] == 0.9
            
            print("✅ 파이프라인 통합 테스트 성공")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
