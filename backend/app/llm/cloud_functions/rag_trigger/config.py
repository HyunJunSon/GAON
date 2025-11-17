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
        return response.payload.data.decode("UTF-8").strip()  # 개행문자 제거
    except Exception as e:
        print(f"Secret 읽기 실패 {secret_name}: {e}")
        return ""


@dataclass
class Settings:
    """Cloud Functions 설정"""
    
    def __post_init__(self):
        # Secret Manager에서 값 읽기
        print("Secret Manager에서 database_url 읽기 시도...")
        self.database_url = get_secret("gaon-database-url")
        print(f"database_url 결과: {self.database_url[:20]}..." if self.database_url else "database_url 실패")
        
        print("Secret Manager에서 openai_api_key 읽기 시도...")
        self.openai_api_key = get_secret("gaon-openai-api-key")
        print(f"openai_api_key 결과: {self.openai_api_key[:20]}..." if self.openai_api_key else "openai_api_key 실패")
    
    # 기본값들
    database_url: str = ""
    openai_api_key: str = ""
    embedding_dimension: int = int(os.getenv('EMBEDDING_DIMENSION', '1536'))
    log_execution_id: bool = os.getenv('LOG_EXECUTION_ID', 'false').lower() == 'true'


settings = Settings()
