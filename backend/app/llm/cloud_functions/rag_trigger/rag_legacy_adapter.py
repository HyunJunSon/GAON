"""
기존 RAG 시스템을 새로운 인터페이스에 맞게 어댑터
"""
from typing import List, Dict, Any, Tuple
from uuid import UUID

from rag_interface import RAGInterface, RAGConfig
from rag import RAGSystem


class LegacyRAGAdapter(RAGInterface):
    """기존 RAG 시스템을 새 인터페이스에 맞게 어댑터"""
    
    def __init__(self, config: RAGConfig):
        super().__init__(config)
        
        # 실제 RAGSystem 초기화
        self.rag_system = RAGSystem(
            storage_type=config.storage_type,
            chunker_type=config.chunker_type,
            **config.extra_config
        )
    
    def load_and_process_file(self, 
                             source_path: str, 
                             **kwargs) -> List[Dict[str, Any]]:
        """파일 로드 및 처리"""
        try:
            results = self.rag_system.load_and_process_file(source_path, **kwargs)
            return results
        except Exception as e:
            return [{"error": f"파일 처리 실패: {str(e)}"}]
    
    def search_similar(self, 
                      query: str, 
                      top_k: int = 5,
                      threshold: float = 0.7,
                      **kwargs) -> List[Dict[str, Any]]:
        """유사도 검색"""
        try:
            results = self.rag_system.search_similar(
                query=query,
                top_k=top_k,
                threshold=threshold,
                **kwargs
            )
            return results
        except Exception as e:
            return [{"error": f"검색 실패: {str(e)}"}]
    
    def add_document(self, 
                    content: str, 
                    metadata: Dict[str, Any] = None) -> str:
        """문서 추가"""
        try:
            doc_id = self.rag_system.add_document(content, metadata)
            return str(doc_id)
        except Exception as e:
            return f"문서 추가 실패: {str(e)}"
    
    def batch_add_documents(self, 
                           documents: List[Tuple[str, Dict[str, Any]]]) -> List[str]:
        """배치 문서 추가"""
        results = []
        for content, metadata in documents:
            try:
                doc_id = self.rag_system.add_document(content, metadata)
                results.append(str(doc_id))
            except Exception as e:
                results.append(f"실패: {str(e)}")
        return results
