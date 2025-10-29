from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from ...core.database import get_db
from . import user_crud, user_schema
from ...utils.logger import auth_logger
from ...utils.exceptions import UserAlreadyExistsException

auth_router = APIRouter(
    prefix="/api/auth",
)


@auth_router.post("/signup", status_code=status.HTTP_204_NO_CONTENT)
def user_create(_user_create: user_schema.UserCreate, db: Session = Depends(get_db)):
    auth_logger.info(f"회원가입 시도: { _user_create.username } - { _user_create.email }")
    
    user = user_crud.get_existing_user(db, user_create=_user_create)
    if user:
        auth_logger.warning(f"중복 사용자로 인한 회원가입 실패: { _user_create.email }")
        raise UserAlreadyExistsException()
    
    user_crud.create_user(db=db, user_create=_user_create)
    auth_logger.info(f"회원가입 성공: { _user_create.username } - { _user_create.email }")
