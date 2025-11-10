# app/core/database_testing.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# ✅ .envt 파일 로드
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_FILE = os.path.join(BASE_DIR, ".envt")  # ✅ .envt

print(f"🔍 [DB] ENV 파일: {ENV_FILE}")
print(f"📁 [DB] 파일 존재: {os.path.exists(ENV_FILE)}")

load_dotenv(ENV_FILE, override=True)

# ✅ DATABASE_URL 읽기
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("⚠️  DATABASE_URL 없음, config_testing 사용")
    from app.core.config_testing import settings_testing as settings
    DATABASE_URL = f"postgresql+psycopg2://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
else:
    print(f"✅ DATABASE_URL 로드 성공")

print(f"🔗 [DB] URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")

# ✅ 엔진 생성
engine_testing = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocalTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine_testing)
Base = declarative_base()


def get_db():
    db = SessionLocalTesting()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    try:
        with engine_testing.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ [DB] 연결 성공!")
    except Exception as e:
        print(f"❌ [DB] 연결 실패: {e}")