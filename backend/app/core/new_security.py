from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..core.config import settings
from ..domains.auth.user_models import User
from ..domains.auth.new_user_crud import new_get_user_by_email
from ..domains.auth.new_user_schema import NewTokenData
from ..utils.exceptions import InvalidCredentialsException
from ..core.database import get_db

# JWT 설정
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

new_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/new_auth/login")


def new_create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def new_verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        new_token_data = NewTokenData(email=email)
    except JWTError:
        raise credentials_exception
    return new_token_data


def new_get_current_user(token: str = Depends(new_oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = InvalidCredentialsException()
    new_token_data = new_verify_token(token, credentials_exception)
    user = new_get_user_by_email(db, email=new_token_data.email)
    if user is None:
        raise credentials_exception
    return user
