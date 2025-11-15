"""
RAG 시스템의 로깅 설정 모듈
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_rag_logging():
    """
    RAG 시스템을 위한 로깅 설정을 구성합니다.
    """
    # 로그 디렉토리 생성
    log_dir = Path("logs/rag")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 로거 생성
    logger = logging.getLogger('rag_system')
    logger.setLevel(logging.DEBUG)
    
    # 기존 핸들러 제거 (다시 설정을 원할 경우)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 포매터 생성
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    # 파일 핸들러 (로테이션)
    file_handler = RotatingFileHandler(
        log_dir / 'rag_system.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 전역 로거 인스턴스
rag_logger = setup_rag_logging()