"""
스토리지 경로 기반 RAG 자동 선택 시스템
클라우드 스토리지 위치에 따라 적절한 RAG 시스템을 자동으로 선택
"""
from typing import Dict, Any, List
from pathlib import Path

from app.llm.rag.implementations.rag_manager import get_rag_manager, RAGType, RAGConfig
from rag_interface import RAGInterface


class RAGAutoSelector:
    """스토리지 경로 기반 RAG 자동 선택기"""
    
    def __init__(self):
        self.manager = get_rag_manager()
        
        # 경로별 RAG 타입 매핑
        self.path_mappings = {
            # 기존 RAG (모든 파일 형식)
            "rag-data/documents/": RAGType.LEGACY,
            
            # TOC 기반 RAG (PDF만)
            "rag-data/toc-pdfs/": RAGType.TOC_BASED,
        }
    
    def select_and_process(self, file_path: str, **kwargs) -> List[Dict[str, Any]]:
        """
        파일 경로를 분석하여 적절한 RAG 시스템을 선택하고 처리
        
        Args:
            file_path: GCS 파일 경로 또는 로컬 파일 경로
            **kwargs: 추가 처리 옵션
            
        Returns:
            처리 결과
        """
        # RAG 타입 결정
        rag_type = self._determine_rag_type(file_path)
        
        # 해당 RAG 시스템으로 교체
        rag = self.manager.switch_to(rag_type, self._get_config_for_type(rag_type))
        
        print(f"📁 경로: {file_path}")
        print(f"🤖 선택된 RAG: {rag_type.value}")
        
        # 파일 처리
        return rag.load_and_process_file(file_path, **kwargs)
    
    def search_with_auto_selection(self, query: str, context_path: str = None, **kwargs) -> List:
        """
        컨텍스트 경로를 고려하여 적절한 RAG로 검색
        
        Args:
            query: 검색 쿼리
            context_path: 컨텍스트 경로 (없으면 기본 RAG 사용)
            **kwargs: 검색 옵션
        """
        if context_path:
            rag_type = self._determine_rag_type(context_path)
            rag = self.manager.switch_to(rag_type, self._get_config_for_type(rag_type))
        else:
            # 기본값: 기존 RAG
            rag = self.manager.switch_to(RAGType.LEGACY)
        
        return rag.search_similar(query, **kwargs)
    
    def generate_advice_if_supported(self, analysis_id: str, **kwargs) -> Dict[str, Any]:
        """
        분석 ID로 조언 생성 (TOC 기반 RAG만 지원)
        """
        # 무조건 TOC 기반 RAG 사용
        rag = self.manager.switch_to(RAGType.TOC_BASED, self._get_config_for_type(RAGType.TOC_BASED))
        
        if not self.manager.is_advanced_rag():
            return {"error": "고급 RAG 기능을 사용할 수 없습니다"}
        
        advanced_rag = self.manager.get_advanced_rag()
        return advanced_rag.generate_advice(analysis_id, **kwargs)
    
    def _determine_rag_type(self, file_path: str) -> RAGType:
        """파일 경로를 분석하여 RAG 타입 결정"""
        # GCS 경로에서 버킷명 제거
        if file_path.startswith("gs://"):
            # gs://bucket-name/path/to/file -> path/to/file
            path_parts = file_path.split("/", 3)
            if len(path_parts) > 3:
                clean_path = path_parts[3]
            else:
                clean_path = file_path
        else:
            clean_path = file_path
        
        # 경로 매핑 확인
        for prefix, rag_type in self.path_mappings.items():
            if clean_path.startswith(prefix):
                return rag_type
        
        # 기본값: 기존 RAG
        return RAGType.LEGACY
    
    def _get_config_for_type(self, rag_type: RAGType) -> RAGConfig:
        """RAG 타입별 설정 반환"""
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
                    "table_name": "ref_handbook_snippet"
                }
            )
        else:
            raise ValueError(f"Unknown RAG type: {rag_type}")
    
    def add_path_mapping(self, path_prefix: str, rag_type: RAGType):
        """새로운 경로 매핑 추가"""
        self.path_mappings[path_prefix] = rag_type
    
    def get_path_mappings(self) -> Dict[str, RAGType]:
        """현재 경로 매핑 반환"""
        return self.path_mappings.copy()


# 전역 인스턴스
_auto_selector = RAGAutoSelector()


def get_rag_auto_selector() -> RAGAutoSelector:
    """RAG 자동 선택기 인스턴스 반환"""
    return _auto_selector


def process_file_with_auto_rag(file_path: str, **kwargs) -> List[Dict[str, Any]]:
    """파일 경로 기반 자동 RAG 처리"""
    return _auto_selector.select_and_process(file_path, **kwargs)


def search_with_auto_rag(query: str, context_path: str = None, **kwargs) -> List:
    """컨텍스트 경로 기반 자동 RAG 검색"""
    return _auto_selector.search_with_auto_selection(query, context_path, **kwargs)
