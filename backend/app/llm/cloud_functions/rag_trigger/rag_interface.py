"""
RAG 시스템 인터페이스 정의
다양한 RAG 구현체를 쉽게 교체할 수 있도록 하는 추상 인터페이스
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from dataclasses import dataclass


@dataclass
class RAGConfig:
    """RAG 시스템 설정"""
    storage_type: str = "local"
    chunker_type: str = "recursive"
    embedding_model: str = "openai"
    vector_db_type: str = "postgresql"
    extra_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_config is None:
            self.extra_config = {}


class RAGInterface(ABC):
    """RAG 시스템의 추상 인터페이스"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
    
    @abstractmethod
    def load_and_process_file(self, 
                             source_path: str, 
                             **kwargs) -> List[Dict[str, Any]]:
        """파일을 로드하고 처리하여 임베딩 생성"""
        pass
    
    @abstractmethod
    def search_similar(self, 
                      query: str, 
                      top_k: int = 5, 
                      threshold: float = 0.5) -> List[Tuple[str, float, UUID]]:
        """유사한 문서 검색"""
        pass
    
    @abstractmethod
    def add_document(self, 
                    text: str, 
                    **kwargs) -> UUID:
        """단일 문서 추가"""
        pass
    
    @abstractmethod
    def batch_add_documents(self, 
                           texts: List[str], 
                           **kwargs) -> List[UUID]:
        """여러 문서 일괄 추가"""
        pass


class AdvancedRAGInterface(RAGInterface):
    """고급 RAG 기능을 위한 확장 인터페이스"""
    
    @abstractmethod
    def search_by_analysis_result(self, 
                                 analysis_id: str, 
                                 **kwargs) -> List[Dict[str, Any]]:
        """분석 결과 기반 검색"""
        pass
    
    @abstractmethod
    def generate_advice(self, 
                       analysis_id: str, 
                       **kwargs) -> Dict[str, Any]:
        """조언 생성"""
        pass
    
    @abstractmethod
    def save_feedback(self, 
                     analysis_id: str, 
                     feedback: str, 
                     **kwargs) -> bool:
        """피드백 저장"""
        pass


class RAGFactory:
    """RAG 시스템 팩토리"""
    
    _implementations = {}
    
    @classmethod
    def register(cls, name: str, implementation_class):
        """RAG 구현체 등록"""
        cls._implementations[name] = implementation_class
    
    @classmethod
    def create(cls, name: str, config: RAGConfig) -> RAGInterface:
        """RAG 시스템 생성"""
        if name not in cls._implementations:
            raise ValueError(f"Unknown RAG implementation: {name}")
        
        return cls._implementations[name](config)
    
    @classmethod
    def list_implementations(cls) -> List[str]:
        """등록된 구현체 목록 반환"""
        return list(cls._implementations.keys())
