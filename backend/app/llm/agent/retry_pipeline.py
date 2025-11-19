"""
재시도 로직이 포함된 Agent 파이프라인
- 단계별 재시도 메커니즘
- 캐시 활용으로 실패한 단계부터 재시작
- LangChain 캐시 시스템 활용
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from langchain.globals import set_llm_cache
from langchain_community.cache import InMemoryCache

from .Cleaner.run_cleaner import run_cleaner
from .Analysis.run_analysis import run_analysis
from .QA.run_qa import run_qa
from .Feedback.run_feedback import run_feedback

logger = logging.getLogger(__name__)

# LangChain 캐시 설정
set_llm_cache(InMemoryCache())


@dataclass
class RetryConfig:
    """재시도 설정"""
    max_retries: int = 3
    base_delay: float = 2.0  # 초기 지연 시간 (초)
    max_delay: float = 60.0  # 최대 지연 시간 (초)
    exponential_base: float = 2.0  # 지수 백오프 배수


@dataclass
class StepResult:
    """단계 실행 결과"""
    step_name: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    attempt: int = 1
    execution_time: float = 0.0
    cached: bool = False


class RetryableAgentPipeline:
    """재시도 가능한 Agent 파이프라인"""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
        self.cache: Dict[str, Any] = {}
        self.step_results: Dict[str, StepResult] = {}
        
    def _get_cache_key(self, step_name: str, conv_id: str) -> str:
        """캐시 키 생성"""
        return f"{step_name}:{conv_id}"
    
    def _get_cached_result(self, step_name: str, conv_id: str) -> Optional[Dict[str, Any]]:
        """캐시된 결과 조회"""
        cache_key = self._get_cache_key(step_name, conv_id)
        return self.cache.get(cache_key)
    
    def _set_cached_result(self, step_name: str, conv_id: str, result: Dict[str, Any]):
        """결과 캐시 저장"""
        cache_key = self._get_cache_key(step_name, conv_id)
        self.cache[cache_key] = result
        logger.info(f"캐시 저장: {cache_key}")
    
    async def _execute_step_with_retry(
        self, 
        step_name: str, 
        step_func, 
        conv_id: str,
        **kwargs
    ) -> StepResult:
        """단계별 재시도 실행"""
        
        # 캐시된 결과 확인
        cached_result = self._get_cached_result(step_name, conv_id)
        if cached_result:
            logger.info(f"캐시된 결과 사용: {step_name}")
            return StepResult(
                step_name=step_name,
                success=True,
                result=cached_result,
                cached=True
            )
        
        last_error = None
        
        for attempt in range(1, self.config.max_retries + 1):
            try:
                start_time = datetime.now()
                logger.info(f"{step_name} 실행 시작 (시도 {attempt}/{self.config.max_retries})")
                
                # 단계 실행
                if step_name in ["cleaner", "analysis", "qa", "feedback"]:
                    if step_name == "cleaner":
                        if conv_id:
                            result = step_func(conv_id=conv_id)
                        else:
                            result = step_func()
                    elif step_name == "analysis":
                        result = step_func(conv_id=conv_id, **kwargs)
                    elif step_name == "qa":
                        result = step_func(conv_id=conv_id, **kwargs)
                    elif step_name == "feedback":                             # ✅ feedback 분기
                        result = step_func(conv_id=conv_id, **kwargs)    
                else:
                    # 테스트용 단계는 직접 실행
                    result = step_func()
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # 성공 시 캐시 저장
                self._set_cached_result(step_name, conv_id, result)
                
                logger.info(f"{step_name} 실행 성공 (시도 {attempt}, {execution_time:.2f}초)")
                
                return StepResult(
                    step_name=step_name,
                    success=True,
                    result=result,
                    attempt=attempt,
                    execution_time=execution_time
                )
                
            except Exception as e:
                last_error = str(e)
                execution_time = (datetime.now() - start_time).total_seconds()
                
                logger.warning(
                    f"{step_name} 실행 실패 (시도 {attempt}/{self.config.max_retries}): {last_error}"
                )
                
                # 마지막 시도가 아니면 지연 후 재시도
                if attempt < self.config.max_retries:
                    delay = min(
                        self.config.base_delay * (self.config.exponential_base ** (attempt - 1)),
                        self.config.max_delay
                    )
                    logger.info(f"{delay:.1f}초 후 재시도...")
                    await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        logger.error(f"{step_name} 최종 실패: {last_error}")
        return StepResult(
            step_name=step_name,
            success=False,
            error=last_error,
            attempt=self.config.max_retries
        )
    
    async def execute_pipeline(self, conv_id: str = None) -> Dict[str, Any]:
        """전체 파이프라인 실행"""
        logger.info(f"재시도 가능한 파이프라인 시작: conv_id={conv_id}")
        
        pipeline_start = datetime.now()
        
        try:
            # 1단계: Cleaner
            cleaner_result = await self._execute_step_with_retry(
                "cleaner", run_cleaner, conv_id or ""
            )
            
            if not cleaner_result.success:
                raise Exception(f"Cleaner 단계 실패: {cleaner_result.error}")
            
            # Cleaner 결과에서 필요한 데이터 추출
            conv_id = cleaner_result.result.get("conv_id")
            user_id = cleaner_result.result.get("id")
            cleaned_df = cleaner_result.result.get("cleaned_df")
            
            # 2단계: Analysis
            analysis_result = await self._execute_step_with_retry(
                "analysis", run_analysis, conv_id,
                id=user_id, conversation_df=cleaned_df
            )
            
            if not analysis_result.success:
                raise Exception(f"Analysis 단계 실패: {analysis_result.error}")
            
            # 3단계: QA
            qa_result = await self._execute_step_with_retry(
                "qa", run_qa, conv_id,
                analysis_result=analysis_result.result["analysis_result"],
                conversation_df=cleaned_df,
                id=user_id
            )

            if not qa_result.success:
                raise Exception(f"QA 단계 실패: {qa_result.error}")

            # 4단계: Feedback ✅ 여기 추가
            analysis_id = analysis_result.result.get("analysis_id")
            feedback_result = await self._execute_step_with_retry(
                "feedback", run_feedback, conv_id,
                id=user_id,
                conversation_df=cleaned_df,
                analysis_id=analysis_id
            )
    
            if not feedback_result.success:
                raise Exception(f"Feedback 단계 실패: {feedback_result.error}")
            
            # 전체 실행 시간
            total_time = (datetime.now() - pipeline_start).total_seconds()
            
            # 최종 결과
            final_result = {
                "status": "completed",
                "conv_id": conv_id,
                "user_id": user_id,
                "analysis_id": analysis_result.result.get("analysis_id"),
                "score": analysis_result.result.get("analysis_result", {}).get("score", 0),
                "confidence": qa_result.result.get("confidence", 0),
                "feedback_json": feedback_result.result.get("advice_text") 
                                or feedback_result.result.get("feedback"),
                "execution_time": total_time,
                "step_results": {
                    "cleaner": {
                        "success": cleaner_result.success,
                        "attempt": cleaner_result.attempt,
                        "cached": cleaner_result.cached,
                        "execution_time": cleaner_result.execution_time
                    },
                    "analysis": {
                        "success": analysis_result.success,
                        "attempt": analysis_result.attempt,
                        "cached": analysis_result.cached,
                        "execution_time": analysis_result.execution_time
                    },
                    "qa": {
                        "success": qa_result.success,
                        "attempt": qa_result.attempt,
                        "cached": qa_result.cached,
                        "execution_time": qa_result.execution_time
                    },
                    "feedback": {
                        "success": feedback_result.success,
                        "attempt": feedback_result.attempt,
                        "cached": feedback_result.cached,
                        "execution_time": feedback_result.execution_time
                    },
                },
            }
            logger.info(f"파이프라인 완료: {total_time:.2f}초")
            return final_result
            
        except Exception as e:
            logger.error(f"파이프라인 실행 실패: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "conv_id": conv_id,
                "execution_time": (datetime.now() - pipeline_start).total_seconds()
            }


# 편의 함수
async def run_agent_pipeline_with_retry(conv_id: str = None) -> Dict[str, Any]:
    """재시도 로직이 포함된 Agent 파이프라인 실행"""
    pipeline = RetryableAgentPipeline()
    return await pipeline.execute_pipeline(conv_id)
