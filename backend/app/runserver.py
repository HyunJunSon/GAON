import uvicorn
import sys
import os

# Add the project root to the Python path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,  # 기본 포트는 8000으로 설정
        reload=True,  # 개발 환경에서 자동 리로드
        log_level="debug",  # 로그 레벨 설정
        access_log=True,  # 접근 로그 활성화
    )