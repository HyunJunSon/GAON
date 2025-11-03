"""
Agent 실행 스크립트

이 스크립트는 Pipeline Manager를 통해 전체 대화 처리 및 분석 파이프라인을 실행합니다.
실행 과정과 결과를 상세히 출력합니다.
"""

import sys
import os
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'pipeline_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger("Agent_Runner")

try:
    from app.llm.Management_Agent.agents.Pipeline_Manager.agent import PipelineManager
except ImportError as e:
    logger.error(f"Import 오류: {str(e)}")
    logger.error("프로젝트 루트 디렉토리에서 스크립트를 실행했는지 확인하세요.")
    sys.exit(1)

def run_pipeline():
    """파이프라인 실행 및 모니터링"""
    try:
        logger.info("=== 파이프라인 실행 시작 ===")
        start_time = datetime.now()
        
        # Pipeline Manager 초기화 및 실행
        pipeline = PipelineManager()
        results = pipeline.run_pipeline()
        
        # 실행 시간 계산
        end_time = datetime.now()
        duration = end_time - start_time
        
        # 실행 통계 출력
        stats = pipeline.get_execution_stats()
        logger.info("\n=== 실행 결과 ===")
        logger.info(f"상태: {stats['status']}")
        logger.info(f"시작 시간: {stats['start_time']}")
        logger.info(f"종료 시간: {stats['end_time']}")
        logger.info(f"총 실행 시간: {duration}")
        
        if stats['errors']:
            logger.warning("\n=== 발생한 오류 ===")
            for error in stats['errors']:
                logger.warning(error)
        
        logger.info("\n=== 파이프라인 실행 완료 ===")
        return results
        
    except Exception as e:
        logger.error(f"\n=== 치명적 오류 발생 ===\n{str(e)}")
        raise

def main():
    """메인 실행 함수"""
    try:
        # 현재 작업 디렉토리 출력
        logger.info(f"현재 작업 디렉토리: {os.getcwd()}")
        
        # 파이프라인 실행
        results = run_pipeline()
        
        # 성공 메시지
        logger.info("\n프로세스가 성공적으로 완료되었습니다.")
        return 0
        
    except Exception as e:
        logger.error(f"\n프로세스 실행 중 오류가 발생했습니다: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)