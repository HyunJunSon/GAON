import logging
import sys
from datetime import datetime
from pathlib import Path

# 로그 디렉토리 생성
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 로깅 포맷 정의
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
)

# 파일 핸들러 생성 (회원가입 관련 로그)
auth_file_handler = logging.FileHandler(log_dir / "auth.log", encoding="utf-8")
auth_file_handler.setLevel(logging.INFO)
auth_file_handler.setFormatter(formatter)

# 일반 로그 파일 핸들러
general_file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
general_file_handler.setLevel(logging.INFO)
general_file_handler.setFormatter(formatter)

# 콘솔 핸들러 생성
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)


def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스를 반환하는 함수"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 중복 핸들러 추가 방지
    if not logger.handlers:
        logger.addHandler(auth_file_handler)
        logger.addHandler(general_file_handler)
        logger.addHandler(console_handler)
    
    # 로그 전파 방지
    logger.propagate = False
    
    return logger


# 인증 관련 로거
auth_logger = get_logger("auth")