from pydantic import BaseModel, EmailStr

# Pydantic 모델은 데이터의 유효성 검사, 직렬화 및 문서화를 지원합니다.

class Token(BaseModel):
    """응답으로 반환될 JWT 토큰 모델"""
    access_token: str  # 액세스 토큰
    token_type: str    # 토큰 타입 (항상 "bearer")
    username: str      # 사용자 이메일

class TokenData(BaseModel):
    """토큰 내부의 데이터를 위한 모델"""
    email: EmailStr | None = None  # 토큰에 포함된 사용자 이메일

class UserLogin(BaseModel):
    """로그인 요청 시 사용될 모델"""
    email: EmailStr  # 사용자 이메일
    password: str    # 사용자 비밀번호

class User(BaseModel):
    """사용자 정보 조회 시 반환될 모델"""
    id: int          # 사용자 ID
    email: EmailStr  # 사용자 이메일
    name: str        # 사용자 이름

    class Config:
        orm_mode = True  # SQLAlchemy 모델과 호환되도록 설정
