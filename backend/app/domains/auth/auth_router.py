from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core import security
from app.domains.auth import auth_service
from app.domains.auth import user_schema
from app.domains.auth import auth_schema as schemas

# API 라우터 설정
router = APIRouter(
    prefix="/api/auth",  # 모든 경로에 /api/auth 접두사 추가
    tags=["Auth"]      # API 문서에서 "Auth" 태그로 그룹화
)


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=user_schema.UserResponse)
def signup(
    user_create: user_schema.UserCreate, 
    db: Session = Depends(get_db)
):
    """
    새로운 사용자를 생성(회원가입)합니다.

    - **name**: 사용자 이름
    - **email**: 사용자 이메일
    - **password**: 사용자 비밀번호
    - **confirmPassword**: 비밀번호 확인
    """
    return auth_service.create_user_service(db=db, user_create=user_create)


@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    사용자 로그인을 처리하고 액세스 토큰을 발급합니다.

    - **email**: 사용자 이메일 (OAuth2에서는 `username` 필드 사용)
    - **password**: 사용자 비밀번호
    """
    # auth_service의 함수를 호출하여 로그인 로직 수행
    return auth_service.login_for_access_token(db=db, form_data=form_data)


@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(security.get_current_user)):
    """
    인증된 현재 사용자의 정보를 반환합니다.
    `get_current_user` 의존성에 의해 토큰이 유효한지 검사됩니다.
    """
    return current_user
