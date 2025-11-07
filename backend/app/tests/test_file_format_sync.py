import pytest
from app.domains.conversation.schemas import ALLOWED_FILE_TYPES, MAX_FILE_SIZE


def test_allowed_file_types():
    """백엔드에서 지원하는 파일 형식 확인"""
    expected_types = {"txt", "pdf", "docx"}
    assert ALLOWED_FILE_TYPES == expected_types


def test_max_file_size():
    """백엔드 최대 파일 크기 확인"""
    expected_size = 50 * 1024 * 1024  # 50MB
    assert MAX_FILE_SIZE == expected_size


def test_file_format_consistency():
    """프론트엔드와 백엔드 파일 형식 일관성 테스트"""
    # 백엔드 지원 형식
    backend_formats = ALLOWED_FILE_TYPES
    
    # 프론트엔드에서 사용해야 할 확장자 (점 포함)
    expected_frontend_extensions = {'.txt', '.pdf', '.docx'}
    
    # 백엔드 형식을 프론트엔드 형식으로 변환
    backend_as_frontend = {f'.{fmt}' for fmt in backend_formats}
    
    assert backend_as_frontend == expected_frontend_extensions


def test_mime_types_mapping():
    """MIME 타입 매핑 확인"""
    expected_mime_mapping = {
        'txt': 'text/plain',
        'pdf': 'application/pdf', 
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    for file_type in ALLOWED_FILE_TYPES:
        assert file_type in expected_mime_mapping, f"MIME type mapping missing for {file_type}"
