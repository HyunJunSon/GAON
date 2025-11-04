from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 데이터베이스 설정 (환경변수에서만 가져오도록 기본값 제거)
    db_user: str = ""
    db_password: str = ""
    db_host: str = ""
    db_port: int = 5432  # PostgreSQL 기본 포트
    db_name: str = ""
    database_url: str = ""

    # 벡터 데이터베이스 설정
    embedding_dimension: int = 1536  # OpenAI embeddings의 기본 차원

    # OpenAI 설정
    openai_api_key: str = ""

    # CORS 설정
    frontend_url: str = "http://localhost:3000"

    # JWT 설정 (운영환경에서는 반드시 변경 필요)
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # LLM 설정
    gemini_api_key: str = ""

    # 환경 변수에서 직접 불러올 수 있도록 설정 추가
    class Config:
        env_file = ".env"
        extra = "ignore"  # 알려지지 않은 변수들은 무시


# 전역 설정 인스턴스
settings = Settings()
