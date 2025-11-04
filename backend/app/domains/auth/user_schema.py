import re
from pydantic import BaseModel, field_validator, EmailStr
from pydantic_core.core_schema import FieldValidationInfo
from ...utils.logger import auth_logger

class UserCreate(BaseModel):
    name: str
    password: str
    email: EmailStr
    terms_agreed: bool

    @field_validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            auth_logger.warning("사용자 이름이 빈 값입니다.")
            raise ValueError('사용자 이름은 빈 값일 수 없습니다.')
        
        # 최소 1자 이상, 최대 20자 이내인지 확인
        if len(v.strip()) < 1 or len(v.strip()) > 20:
            auth_logger.warning(f"사용자 이름 길이가 유효하지 않습니다: {v}")
            raise ValueError('사용자 이름은 1자 이상 20자 이내여야 합니다.')
        
        auth_logger.debug(f"사용자 이름 유효성 검사 통과: {v}")
        return v.strip()

    @field_validator('password')
    def validate_password(cls, v):
        if not v or not v.strip():
            auth_logger.warning("비밀번호가 빈 값입니다.")
            raise ValueError('비밀번호는 빈 값일 수 없습니다.')
        
        # 8~16자, 한글/영문/특수문자 최소 1가지 조합인지 확인
        if not re.match(r'^(?=.*[A-Za-z])(?=.*[ㄱ-ㅎㅏ-ㅣ가-힣])(?=.*[@$!%*#?&])[A-Za-zㄱ-ㅎㅏ-ㅣ가-힣@$!%*#?&]{8,16}$', v):
            auth_logger.warning(f"비밀번호 형식이 유효하지 않습니다: {v}")
            raise ValueError('비밀번호는 8~16자이며, 한글, 영문, 특수문자를 각각 최소 1개 이상 포함해야 합니다.')
        
        auth_logger.debug("비밀번호 유효성 검사 통과")
        return v

    @field_validator('email')
    def validate_email(cls, v):
        if not v or not v.strip():
            auth_logger.warning("이메일이 빈 값입니다.")
            raise ValueError('이메일은 빈 값일 수 없습니다.')
        
        # 이메일 형식 확인
        if not re.match(r'^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', v):
            auth_logger.warning(f"이메일 형식이 유효하지 않습니다: {v}")
            raise ValueError('올바른 이메일 형식이 아닙니다.')
        
        auth_logger.debug(f"이메일 유효성 검사 통과: {v}")
        return v

    @field_validator('terms_agreed')
    def validate_terms_agreed(cls, v):
        if v is not True:
            auth_logger.warning("약관 동의가 필요합니다.")
            raise ValueError('회원가입을 위해 약관에 동의해야 합니다.')
        return v


class UserResponse(BaseModel):
    """회원가입 성공 시 반환될 모델"""
    user_id: int
