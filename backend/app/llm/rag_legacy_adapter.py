"""
기존 RAG 시스템을 새로운 인터페이스에 맞게 어댑터
"""
from typing import List, Dict, Any, Tuple
from uuid import UUID

from .rag_interface import RAGInterface, RAGConfig
from .rag import RAGSystem


class LegacyRAGAdapter(RAGInterface):
    """기존 RAG 시스템을 새 인터페이스에 맞게 어댑터"""
    
    def __init__(self, config: RAGConfig):
        super().__init__(config)
        
        # 기존 RAGSystem 초기화
        self.rag_system = RAGSystem(
            storage_type=config.storage_type,
            chunker_type=config.chunker_type,
            **config.extra_config
        )
    
    def load_and_process_file(self, 
                             source_path: str, 
                             **kwargs) -> List[Dict[str, Any]]:
        """파일을 로드하고 처리하여 임베딩 생성"""
        chunk_kwargs = kwargs.get('chunk_kwargs', {})
        return self.rag_system.load_and_process_file(source_path, chunk_kwargs)
    
    def search_similar(self, 
                      query: str, 
                      top_k: int = 5, 
                      threshold: float = 0.5) -> List[Tuple[str, float, UUID]]:
        """유사한 문서 검색"""
        return self.rag_system.search_similar(query, top_k, threshold)
    
    def add_document(self, 
                    text: str, 
                    **kwargs) -> UUID:
        """단일 문서 추가"""
        book_id = kwargs.get('book_id')
        metadata = kwargs.get('metadata')
        return self.rag_system.add_document(text, book_id, metadata)
    
    def batch_add_documents(self, 
                           texts: List[str], 
                           **kwargs) -> List[UUID]:
        """여러 문서 일괄 추가"""
        book_ids = kwargs.get('book_ids')
        metadata_list = kwargs.get('metadata_list')
        return self.rag_system.batch_add_documents(texts, book_ids, metadata_list)
