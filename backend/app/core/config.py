from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 데이터베이스 설정
    db_user: str = ""
    db_password: str = ""
    db_host: str = "localhost"
    db_port: int = 1111
    db_name: str = ""

    # CORS 설정
    frontend_url: str = "http://localhost:3000"

    # JWT 설정
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # LLM 설정
    gemini_api_key: str = ""

    # LangChain 설정
    langchain_tracing_v2: str = "false"
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_project: str = "Gaon"
    langchain_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"  # 알려지지 않은 변수들은 무시


# 전역 설정 인스턴스
settings = Settings()
