from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from .new_user_schema import NewUserCreate
from .user_models import User
from passlib.context import CryptContext
from ...utils.logger import auth_logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def new_create_user(db: Session, user_create: NewUserCreate):
    auth_logger.info(f"DB에 사용자 생성 시작: { user_create.email }")
    db_user = User(
        name=user_create.name,
        password=pwd_context.hash(user_create.password.encode('utf-8')),
        email=user_create.email,
        create_date=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    auth_logger.info(f"DB에 사용자 생성 완료: { user_create.email }")


def new_get_existing_user(db: Session, user_create: NewUserCreate):
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

def new_get_user_by_email(db: Session, email: str) -> Optional[User]:
    auth_logger.debug(f"이메일로 사용자 조회 시도: {email}")
    return db.query(User).filter(User.email == email).first()

def new_get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    auth_logger.debug(f"ID로 사용자 조회 시도: {user_id}")
    return db.query(User).filter(User.id == user_id).first()

def new_delete_user(db: Session, user: User):
    auth_logger.info(f"DB에서 사용자 삭제 시작: {user.email}")
    db.delete(user)
    db.commit()
    auth_logger.info(f"DB에서 사용자 삭제 완료: {user.email}")

def new_authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    auth_logger.debug(f"사용자 인증 시도: {email}")
    user = new_get_user_by_email(db, email)
    if not user or not pwd_context.verify(password.encode('utf-8'), user.password):
        auth_logger.warning(f"인증 실패: {email}")
        return None
    auth_logger.info(f"사용자 인증 성공: {email}")
    return user

def new_update_user_password(db: Session, user: User, new_password: str):
    auth_logger.info(f"사용자 비밀번호 업데이트 시작: {user.email}")
    user.password = pwd_context.hash(new_password.encode('utf-8'))
    db.add(user)
    db.commit()
    auth_logger.info(f"사용자 비밀번호 업데이트 완료: {user.email}")

def new_update_user_email(db: Session, user: User, new_email: str):
    auth_logger.info(f"사용자 이메일 업데이트 시작: {user.email}")
    user.email = new_email
    db.add(user)
    db.commit()
    auth_logger.info(f"사용자 이메일 업데이트 완료: {user.email}")
