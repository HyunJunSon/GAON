from datetime import timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import security
from app.core.database import get_db
from app.domains.auth import user_crud
from app.domains.auth import user_schema
from app.domains.auth import auth_schema as schemas


def create_user_service(db: Session, user_create: user_schema.UserCreate):
    """
    새로운 사용자를 생성하는 서비스 함수.
    - 이메일 중복 여부를 확인합니다.
    - 중복되지 않은 경우, 새로운 사용자를 생성합니다.
    """
    # 이메일로 기존 사용자 조회
    existing_user = user_crud.get_user_by_email(db, email=user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용중인 이메일입니다.",
        )
    
    # 새로운 사용자 생성
    return user_crud.create_user(db=db, user_create=user_create)


def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> schemas.Token:
    """
    사용자를 인증하고 액세스 토큰을 반환합니다.
    OAuth2PasswordRequestForm은 'username'과 'password' 필드를 가집니다.
    여기서는 'username'을 이메일로 사용합니다.
    """
    # 이메일(form_data.username)을 사용하여 사용자 정보 조회
    user = user_crud.get_user_by_email(db, email=form_data.username)
    
    # 사용자가 없거나 비밀번호가 일치하지 않으면 인증 오류 발생
    if not user or not security.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 잘못되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 액세스 토큰 만료 시간 설정
    access_token_expires = timedelta(minutes=security.settings.access_token_expire_minutes)
    
    # 액세스 토큰 생성 (페이로드에 사용자 이메일 포함)
    access_token = security.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    # 최종적으로 Token 스키마에 맞춰 응답 반환
    return schemas.Token(
        access_token=access_token,
        token_type="bearer",
        username=user.email
    )


def logout(token: str = Depends(security.oauth2_scheme)):
    """
    제공된 토큰을 블랙리스트에 추가하여 로그아웃 처리합니다.
    """
    security.blacklist.add(token)
    return {"message": "성공적으로 로그아웃되었습니다."}
