import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .config import settings


# PostgreSQL 데이터베이스 연결 설정 (pgvector 지원 포함)
DATABASE_URL = f"postgresql+psycopg2://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

# 데이터베이스 엔진 생성 - 연결 풀 설정 포함
engine = create_engine(
    DATABASE_URL,
    pool_size=10,              # 연결 풀 크기
    max_overflow=20,           # 최대 오버플로우 연결
    pool_pre_ping=True,        # 연결 확인
    pool_recycle=300,          # 연결 재사용 시간(초)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

