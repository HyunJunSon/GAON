"""
RAG 시스템의 예외 처리 모듈
"""
from .logger import rag_logger


class RAGException(Exception):
    """
    RAG 시스템 전용 예외 클래스
    """
    def __init__(self, message: str, error_code: str = None, original_exception: Exception = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.original_exception = original_exception
        
        # 로그 기록
        rag_logger.error(f"RAGException 발생 - 코드: {error_code}, 메시지: {message}")
        if original_exception:
            rag_logger.error(f"원본 예외: {str(original_exception)}")


class DocumentLoadException(RAGException):
    """
    문서 로드 관련 예외
    """
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message, error_code="DOC_LOAD_ERROR", original_exception=original_exception)


class ExtractionException(RAGException):
    """
    문서 추출 관련 예외
    """
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message, error_code="EXTRACT_ERROR", original_exception=original_exception)


class ChunkingException(RAGException):
    """
    문서 청킹 관련 예외
    """
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message, error_code="CHUNK_ERROR", original_exception=original_exception)


class StorageException(RAGException):
    """
    저장소 관련 예외
    """
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message, error_code="STORAGE_ERROR", original_exception=original_exception)


class VectorDBException(RAGException):
    """
    벡터 DB 관련 예외
    """
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message, error_code="VECTOR_DB_ERROR", original_exception=original_exception)


class EmbeddingException(RAGException):
    """
    임베딩 생성 관련 예외
    """
    def __init__(self, message: str, original_exception: Exception = None):
        super().__init__(message, error_code="EMBEDDING_ERROR", original_exception=original_exception)