"""
RAG 시스템 매니저
다양한 RAG 구현체를 통합 관리하고 쉽게 교체할 수 있도록 하는 매니저
"""
from typing import Dict, Any, Optional
from enum import Enum

from rag_interface import RAGInterface, AdvancedRAGInterface, RAGConfig, RAGFactory
from rag_legacy_adapter import LegacyRAGAdapter

# TOC RAG는 현재 사용하지 않으므로 더미 클래스로 대체
class TOCBasedRAG(RAGInterface):
    def __init__(self, config):
        super().__init__(config)
    
    def load_and_process_file(self, source_path, **kwargs):
        return [{"message": "TOC RAG는 현재 사용하지 않습니다"}]
    
    def search_similar(self, query, **kwargs):
        return []
    
    def add_document(self, content, metadata=None):
        return "toc-dummy"


class RAGType(Enum):
    """RAG 시스템 타입"""
    LEGACY = "legacy"
    TOC_BASED = "toc_based"


class RAGManager:
    """RAG 시스템 통합 매니저"""
    
    def __init__(self):
        self._current_rag: Optional[RAGInterface] = None
        self._current_type: Optional[RAGType] = None
        self._register_implementations()
    
    def _register_implementations(self):
        """RAG 구현체들을 팩토리에 등록"""
        RAGFactory.register(RAGType.LEGACY.value, LegacyRAGAdapter)
        RAGFactory.register(RAGType.TOC_BASED.value, TOCBasedRAG)
    
    def switch_to(self, rag_type: RAGType, config: Optional[RAGConfig] = None) -> RAGInterface:
        """RAG 시스템 교체"""
        if config is None:
            config = self._get_default_config(rag_type)
        
        self._current_rag = RAGFactory.create(rag_type.value, config)
        self._current_type = rag_type
        
        return self._current_rag
    
    def get_current(self) -> Optional[RAGInterface]:
        """현재 활성화된 RAG 시스템 반환"""
        return self._current_rag
    
    def get_current_type(self) -> Optional[RAGType]:
        """현재 RAG 시스템 타입 반환"""
        return self._current_type
    
    def is_advanced_rag(self) -> bool:
        """현재 RAG가 고급 기능을 지원하는지 확인"""
        return isinstance(self._current_rag, AdvancedRAGInterface)
    
    def get_advanced_rag(self) -> Optional[AdvancedRAGInterface]:
        """고급 RAG 인터페이스 반환 (지원하는 경우)"""
        if self.is_advanced_rag():
            return self._current_rag
        return None
    
    def _get_default_config(self, rag_type: RAGType) -> RAGConfig:
        """RAG 타입별 기본 설정 반환"""
        if rag_type == RAGType.LEGACY:
            return RAGConfig(
                storage_type="gcp",
                chunker_type="recursive",
                embedding_model="openai",
                vector_db_type="postgresql",
                extra_config={
                    "bucket_name": "gaon-cloud-data"
                }
            )
        elif rag_type == RAGType.TOC_BASED:
            return RAGConfig(
                storage_type="gcp",
                chunker_type="toc_based",
                embedding_model="openai",
                vector_db_type="postgresql",
                extra_config={
                    "bucket_name": "gaon-cloud-data",
                    "embedding_model": "text-embedding-3-small",
                    "table_name": "ideal_answer"
                }
            )
        else:
            raise ValueError(f"Unknown RAG type: {rag_type}")


# 전역 RAG 매니저 인스턴스
rag_manager = RAGManager()


def get_rag_manager() -> RAGManager:
    """RAG 매니저 인스턴스 반환"""
    return rag_manager


def get_current_rag() -> Optional[RAGInterface]:
    """현재 활성화된 RAG 시스템 반환"""
    return rag_manager.get_current()


def switch_rag(rag_type: RAGType, config: Optional[RAGConfig] = None) -> RAGInterface:
    """RAG 시스템 교체"""
    return rag_manager.switch_to(rag_type, config)
