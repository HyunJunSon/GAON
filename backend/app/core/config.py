from typing import Optional, List
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    # 데이터베이스 설정
    db_user: str = ""
    db_password: str = ""
    db_host: str = ""
    db_port: int = 5432
    db_name: str = ""
    database_url: str = ""

    embedding_dimension: int = 1536

    openai_api_key: str = ""
    frontend_url: str = "http://localhost:3000"

    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    max_file_size: int = 10 * 1024 * 1024
    allowed_file_types: List[str] = ["pdf", "txt", "docx", "epub", "md"]

    gemini_api_key: str = ""

    langchain_tracing_v2: str = "false"
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_project: str = "Gaon"
    langchain_api_key: str = ""

    huggingface_token: str = ""
    assemblyai_api_key: str = ""

    # ⭐ GCP 관련 설정
    google_application_credentials: str = ""
    gcp_bucket_name: str = ""

    class Config:
        env_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
        )
        extra = "ignore"


# -------------------------
# 전역 설정 인스턴스 생성
# -------------------------
settings = Settings()


# ==========================================================
# ⭐ 1) GCP Credential 절대경로 자동 변환 (핵심 코드)
# ==========================================================
if settings.google_application_credentials:
    raw_path = settings.google_application_credentials

    # 프로젝트 루트 폴더
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # 상대경로라면 절대경로로 변환
    if not os.path.isabs(raw_path):
        abs_path = os.path.join(BASE_DIR, raw_path)
    else:
        abs_path = raw_path

    # OS 경로 normalize
    abs_path = os.path.normpath(abs_path)

    # 환경변수에 적용
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_path

    print(f"🔑 [GCP] GOOGLE_APPLICATION_CREDENTIALS set to: {abs_path}")


# ==========================================================
# ⭐ 2) LangChain 관련 환경변수 설정
# ==========================================================
if settings.langchain_tracing_v2.lower() == "true":
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    if settings.langchain_api_key:
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
