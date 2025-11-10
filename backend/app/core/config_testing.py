# app/core/config_testing.py
from typing import Optional
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

# ✅ .envt 파일 로드
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE = os.path.join(BASE_DIR, ".envt")  # ✅ .envt

print(f"🔍 [Config] ENV 파일: {ENV_FILE}")
print(f"📁 [Config] 파일 존재: {os.path.exists(ENV_FILE)}")

load_dotenv(ENV_FILE, override=True)


class Settings(BaseSettings):
    # 데이터베이스 설정
    db_user: str = ""
    db_password: str = ""
    db_host: str = ""
    db_port: int = 5433
    db_name: str = ""
    database_url: str = ""

    # 벡터 데이터베이스 설정
    embedding_dimension: int = 1536

    # OpenAI 설정
    openai_api_key: str = ""

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
        extra = "ignore"


# ✅ 전역 설정 인스턴스
settings_testing = Settings()


if __name__ == "__main__":
    print(f"✅ settings_testing 생성됨")
    print(f"DATABASE_URL: {settings_testing.database_url}")