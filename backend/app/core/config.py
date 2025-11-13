from typing import Optional, List
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

    # JWT 설정 (⚠️ 운영환경에서는 반드시 강력한 키로 변경 필요)
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # 파일 업로드 설정
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = ["pdf", "txt", "docx", "epub", "md"]

    # LLM 설정
    gemini_api_key: str = ""

    # LangChain 설정
    langchain_tracing_v2: str = "false"
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_project: str = "Gaon"
    langchain_api_key: str = ""

    # Hugging Face 설정
    huggingface_token: str = ""
    
    # 화자분리 서비스 설정
    assemblyai_api_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"  # 알려지지 않은 변수들은 무시


# 전역 설정 인스턴스
settings = Settings()
