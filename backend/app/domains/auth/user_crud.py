from sqlalchemy.orm import Session
from .user_schema import UserCreate
from .user_models import User
from app.core.security import hash_password
from app.utils.logger import auth_logger
from datetime import datetime


def create_user(db: Session, user_create: UserCreate):
    auth_logger.info(f"DB에 사용자 생성 시작: { user_create.email }")
    db_user = User(
        name=user_create.name,
        password=hash_password(user_create.password),
        email=user_create.email,
        create_date=datetime.now(),
        terms_agreed=user_create.terms_agreed,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    auth_logger.info(f"DB에 사용자 생성 완료: { user_create.email }")
    return db_user


def get_user_by_email(db: Session, email: str):
    """이메일을 사용하여 데이터베이스에서 사용자를 조회합니다."""
    auth_logger.debug(f"사용자 검색 시도: {email}")
    user = db.query(User).filter(User.email == email).first()
    if user:
        auth_logger.info(f"사용자 발견: {user.email}")
    else:
        auth_logger.debug(f"사용자를 찾을 수 없음: {email}")
    return user


def get_existing_user(db: Session, user_create: UserCreate):
    auth_logger.debug(f"기존 사용자 확인 시도: { user_create.email }")
    user = (
        db.query(User)
        .filter(
            (User.name == user_create.name) | (User.email == user_create.email)
        )
        .first()
    )
    if user:
        auth_logger.info(f"기존 사용자 발견: { user.email if user else 'None' }")
    else:
        auth_logger.debug(f"신규 사용자 확인: { user_create.email }")
    return user
