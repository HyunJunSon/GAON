from fastapi import HTTPException, status


class UserException(HTTPException):
    """사용자 관련 예외의 기본 클래스"""
    pass


class UserAlreadyExistsException(UserException):
    """이미 존재하는 사용자일 때 발생하는 예외"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 존재하는 사용자입니다."
        )


class UserNotFoundException(UserException):
    """사용자를 찾을 수 없을 때 발생하는 예외"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )


class InvalidCredentialsException(UserException):
    """잘못된 자격 증명일 때 발생하는 예외"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="잘못된 자격 증명입니다."
        )


class ValidationErrorException(UserException):
    """유효성 검사 오류가 발생할 때 발생하는 예외"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )