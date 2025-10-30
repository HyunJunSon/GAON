from sqlalchemy.orm import Session
from .user_schema import UserCreate
from .user_models import User
from passlib.context import CryptContext
from ...utils.logger import auth_logger


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user(db: Session, user_create: UserCreate):
    auth_logger.info(f"DB에 사용자 생성 시작: { user_create.email }")
    db_user = User(
        name=user_create.name,
        password=pwd_context.hash(user_create.password),
        email=user_create.email,
    )
    db.add(db_user)
    db.commit()
    auth_logger.info(f"DB에 사용자 생성 완료: { user_create.email }")


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
