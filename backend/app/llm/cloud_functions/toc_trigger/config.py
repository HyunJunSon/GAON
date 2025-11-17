"""
Cloud Functions용 설정
"""
import os
from dataclasses import dataclass
from google.cloud import secretmanager


def get_secret(secret_name: str) -> str:
    """Secret Manager에서 값 가져오기"""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/gaon-477004/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8").strip()
    except Exception as e:
        print(f"Secret 읽기 실패 {secret_name}: {e}")
        return ""


def get_secret_from_env_or_direct(env_key: str, secret_name: str) -> str:
    """환경변수에서 Secret Manager 경로를 가져오거나 직접 Secret 읽기"""
    env_value = os.getenv(env_key, "")
    
    # 환경변수가 Secret Manager 경로인지 확인
    if env_value.startswith("projects/") and "/secrets/" in env_value:
        # Secret Manager 경로에서 실제 값 읽기
        try:
            client = secretmanager.SecretManagerServiceClient()
            response = client.access_secret_version(request={"name": env_value})
            return response.payload.data.decode("UTF-8").strip()
        except Exception as e:
            print(f"환경변수 Secret 읽기 실패 {env_key}: {e}")
            return ""
    elif env_value:
        # 일반 환경변수 값
        return env_value
    else:
        # 직접 Secret Manager에서 읽기
        return get_secret(secret_name)


@dataclass
class Settings:
    """Cloud Functions 설정"""
    
    def __post_init__(self):
        # 환경변수 또는 Secret Manager에서 값 읽기
        print("database_url 읽기 시도...")
        self.database_url = get_secret_from_env_or_direct("DATABASE_URL", "gaon-database-url")
        print("database_url 읽기 완료" if self.database_url else "database_url 실패")
        
        print("openai_api_key 읽기 시도...")
        self.openai_api_key = get_secret_from_env_or_direct("OPENAI_API_KEY", "gaon-openai-api-key")
        print("openai_api_key 읽기 완료" if self.openai_api_key else "openai_api_key 실패")
    
    # 기본값들
    database_url: str = ""
    openai_api_key: str = ""
    embedding_dimension: int = int(os.getenv('EMBEDDING_DIMENSION', '1536'))
    log_execution_id: bool = os.getenv('LOG_EXECUTION_ID', 'false').lower() == 'true'


settings = Settings()
