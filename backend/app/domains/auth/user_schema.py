import re
from pydantic import BaseModel, field_validator, EmailStr
from pydantic_core.core_schema import FieldValidationInfo
from ...utils.logger import auth_logger

class UserCreate(BaseModel):
    name: str
    password: str
    confirmPassword: str
    email: EmailStr

    @field_validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            auth_logger.warning("사용자 이름이 빈 값입니다.")
            raise ValueError('사용자 이름은 빈 값일 수 없습니다.')
        
        # 최소 1자 이상, 최대 20자 이내인지 확인
        if len(v.strip()) < 1 or len(v.strip()) > 20:
            auth_logger.warning(f"사용자 이름 길이가 유효하지 않습니다: {v}")
            raise ValueError('사용자 이름은 1자 이상 20자 이내여야 합니다.')
        
        # 한글 또는 영어만 포함하는지 확인
        if not re.match(r'^[가-힣a-zA-Z]{1,20}$', v.strip()):
            auth_logger.warning(f"사용자 이름 형식이 잘못되었습니다: {v}")
            raise ValueError('사용자 이름은 한글 또는 영어로만 구성되어야 합니다.')
        
        auth_logger.debug(f"사용자 이름 유효성 검사 통과: {v}")
        return v.strip()

    @field_validator('password')
    def validate_password(cls, v):
        if not v or not v.strip():
            auth_logger.warning("비밀번호가 빈 값입니다.")
            raise ValueError('비밀번호는 빈 값일 수 없습니다.')
        
        # 8~16자, 영문/숫자/특수문자 최소 1가지 조합인지 확인
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,16}$', v):
            auth_logger.warning(f"비밀번호 형식이 유효하지 않습니다: {v}")
            raise ValueError('비밀번호는 8~16자이며, 영문, 숫자, 특수문자를 각각 최소 1개 이상 포함해야 합니다.')
        
        auth_logger.debug("비밀번호 유효성 검사 통과")
        return v

    @field_validator('confirmPassword')
    def validate_confirm_password(cls, v, info: FieldValidationInfo):
        if not v or not v.strip():
            auth_logger.warning("비밀번호 확인이 빈 값입니다.")
            raise ValueError('비밀번호 확인은 빈 값일 수 없습니다.')
        
        # password와 일치하는지 확인
        if 'password' in info.data and v != info.data['password']:
            auth_logger.warning("비밀번호가 일치하지 않습니다.")
            raise ValueError('비밀번호가 일치하지 않습니다.')
        
        # password의 유효성 검사도 수행
        password = info.data.get('password')
        if password and not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,16}$', password):
            auth_logger.warning("비밀번호 형식이 유효하지 않습니다.")
            raise ValueError('비밀번호는 8~16자이며, 영문, 숫자, 특수문자를 각각 최소 1개 이상 포함해야 합니다.')
        
        # confirmPassword에 대한 유효성 검사
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,16}$', v):
            auth_logger.warning("비밀번호 확인 형식이 유효하지 않습니다.")
            raise ValueError('비밀번호 확인은 8~16자이며, 영문, 숫자, 특수문자를 각각 최소 1개 이상 포함해야 합니다.')
        
        auth_logger.debug("비밀번호 확인 유효성 검사 통과")
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


class UserResponse(BaseModel):
    """회원가입 성공 시 반환될 모델"""
    email: EmailStr
    name: str

    class Config:
        from_attributes = True  # Pydantic V2에서는 orm_mode 대신 from_attributes 사용
