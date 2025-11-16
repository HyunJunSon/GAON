from typing import Optional, List
from pydantic_settings import BaseSettings
import os


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
        # 절대 경로로 .env 파일 지정
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        extra = "ignore"  # 알려지지 않은 변수들은 무시


# 전역 설정 인스턴스
settings = Settings()

# LangChain 환경변수 설정 (LangChain이 자동으로 읽을 수 있도록)
if settings.langchain_tracing_v2.lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    if settings.langchain_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
