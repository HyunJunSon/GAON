import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db

# 테스트용 인-메모리 SQLite 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 각 테스트 함수에 독립적인, 완전히 비어있는 DB 세션을 제공하는 fixture
@pytest.fixture(scope="function")
def db_session():
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    # 의존성 오버라이드를 통해 get_db가 테스트용 DB 세션을 반환하도록 설정
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        # 테스트가 끝나면 모든 테이블을 삭제하여 다음 테스트에 영향을 주지 않도록 합니다.
        session.close()
        Base.metadata.drop_all(bind=engine)
        app.dependency_overrides.pop(get_db, None)

# 모든 테스트에서 사용할 수 있는 TestClient fixture
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
