from app.core.config import settings

def check_db_settings():
    """현재 설정된 데이터베이스 연결 정보 확인"""
    print("\n=== 현재 데이터베이스 설정 ===")
    print(f"호스트: {settings.db_host}")
    print(f"포트: {settings.db_port}")
    print(f"데이터베이스: {settings.db_name}")
    print(f"사용자: {settings.db_user}")
    print(f"비밀번호: {'*' * len(settings.db_password) if settings.db_password else '설정되지 않음'}")

if __name__ == "__main__":
    check_db_settings()