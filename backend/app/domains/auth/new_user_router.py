from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.new_security import new_create_access_token, new_get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from . import user_crud
from .new_user_crud import new_create_user, new_get_existing_user, new_authenticate_user, new_delete_user
from .new_user_schema import NewUserCreate, NewToken, NewUserDelete
from .user_models import User
from ...utils.logger import auth_logger
from ...utils.exceptions import UserAlreadyExistsException, InvalidCredentialsException, UserNotFoundException

new_auth_router = APIRouter(
    prefix="/api/new_auth",
)


@new_auth_router.post("/signup", status_code=status.HTTP_204_NO_CONTENT)
def new_user_create(_user_create: NewUserCreate, db: Session = Depends(get_db)):
    auth_logger.info(f"회원가입 시도: { _user_create.name } - { _user_create.email }")
    
    user = new_get_existing_user(db, user_create=_user_create)
    if user:
        auth_logger.warning(f"중복 사용자로 인한 회원가입 실패: { _user_create.email }")
        raise UserAlreadyExistsException()
    
    new_create_user(db=db, user_create=_user_create)
    auth_logger.info(f"회원가입 성공: { _user_create.name } - { _user_create.email }")


@new_auth_router.post("/login", response_model=NewToken)
def new_login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    auth_logger.info(f"로그인 시도: {form_data.username}")
    user = new_authenticate_user(db, form_data.username, form_data.password)
    if not user:
        auth_logger.warning(f"로그인 실패: 잘못된 자격 증명 - {form_data.username}")
        raise InvalidCredentialsException()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = new_create_access_token(
        data={
            "sub": user.email,
            "id": user.id,
            "name": user.name
        },
        expires_delta=access_token_expires
    )
    auth_logger.info(f"로그인 성공: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@new_auth_router.delete("/user", status_code=status.HTTP_204_NO_CONTENT)
def new_delete_user_api(user_delete: NewUserDelete, current_user: User = Depends(new_get_current_user), db: Session = Depends(get_db)):
    auth_logger.info(f"회원 탈퇴 시도: {current_user.email}")
    
    # 비밀번호 확인
    if not user_crud.pwd_context.verify(user_delete.password.encode('utf-8'), current_user.password):
        auth_logger.warning(f"회원 탈퇴 실패: 비밀번호 불일치 - {current_user.email}")
        raise InvalidCredentialsException()
    
    new_delete_user(db, current_user)
    auth_logger.info(f"회원 탈퇴 성공: {current_user.email}")
