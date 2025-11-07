from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.domains.auth import user_crud
from app.domains.auth import auth_schema as schemas

# OAuth2 비밀번호 인증 스키마 설정, tokenUrl은 토큰을 얻기 위한 엔드포인트를 가리킵니다.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ⚠️ 메모리 내 토큰 블랙리스트 - 프로덕션에서는 Redis/DB 사용 필수
# 현재 구현은 서버 재시작 시 블랙리스트가 초기화되는 문제가 있음
blacklist = set()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """새로운 액세스 토큰을 생성합니다."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # 설정 파일에서 만료 시간을 가져와 기본 만료 시간 설정
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode.update({"exp": expire})
    # JWT 토큰 인코딩
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> schemas.User:
    """
    액세스 토큰을 디코딩하고 유효성을 검사하여 현재 사용자를 반환합니다.
    토큰이 유효하지 않거나, 만료되었거나, 블랙리스트에 포함된 경우 HTTPException을 발생시킵니다.
    """
    # 토큰이 블랙리스트에 있는지 확인
    if token in blacklist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰이 블랙리스트에 등록되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 자격 증명 유효성 검사 실패 시 발생시킬 예외
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="자격 증명을 확인할 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 토큰 디코딩
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception

    # 데이터베이스에서 사용자 조회
    user = user_crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user
