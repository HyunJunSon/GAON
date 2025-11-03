"""
Pipeline Manager Agent

이 에이전트는 전체 대화 처리 파이프라인을 관리하는 상위 에이전트입니다.
Conversation Builder와 Conversation Analyzer를 순차적으로 실행하고
전체 프로세스를 조율합니다.

주요 기능:
1. 전체 파이프라인 실행 관리
2. 에이전트 간 데이터 흐름 조정
3. 에러 처리 및 로깅
4. 실행 상태 모니터링

입력: test_raw_conversation 테이블 데이터
출력: conversation 테이블 데이터 및 conversation_analysis.json
"""

import logging
from datetime import datetime
from typing import Dict, Any

from ..Conversation_Builder.agent import ConversationBuilder
from ..Conversation_Analyzer.agent import ConversationAnalyzer

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Pipeline_Manager")

class PipelineManager:
    def __init__(self):
        """PipelineManager 초기화"""
        self.builder = ConversationBuilder()
        self.analyzer = ConversationAnalyzer()
        self.execution_stats = {
            "start_time": None,
            "end_time": None,
            "status": "not_started",
            "errors": []
        }

    def run_pipeline(self) -> Dict[str, Any]:
        """전체 파이프라인 실행"""
        self.execution_stats["start_time"] = datetime.now()
        self.execution_stats["status"] = "running"
        
        try:
            # 1. Conversation Builder 실행
            logger.info("Starting Conversation Builder")
            self.builder.run()
            
            # 2. Conversation Analyzer 실행
            logger.info("Starting Conversation Analyzer")
            analysis_results = self.analyzer.run()
            
            self.execution_stats["status"] = "completed"
            logger.info("Pipeline completed successfully")
            
            return analysis_results
            
        except Exception as e:
            self.execution_stats["status"] = "failed"
            self.execution_stats["errors"].append(str(e))
            logger.error(f"Pipeline failed: {str(e)}")
            raise
        
        finally:
            self.execution_stats["end_time"] = datetime.now()
            self._log_execution_stats()

    def _log_execution_stats(self):
        """실행 통계 로깅"""
        if self.execution_stats["start_time"] and self.execution_stats["end_time"]:
            duration = self.execution_stats["end_time"] - self.execution_stats["start_time"]
            logger.info(f"""
Pipeline Execution Statistics:
- Status: {self.execution_stats['status']}
- Duration: {duration}
- Start Time: {self.execution_stats['start_time']}
- End Time: {self.execution_stats['end_time']}
- Errors: {len(self.execution_stats['errors'])}
            """)

    def get_execution_stats(self) -> Dict[str, Any]:
        """실행 통계 반환"""
        return self.execution_stats

if __name__ == "__main__":
    pipeline = PipelineManager()
    try:
        results = pipeline.run_pipeline()
        print("Pipeline executed successfully")
    except Exception as e:
        print(f"Pipeline failed: {str(e)}")