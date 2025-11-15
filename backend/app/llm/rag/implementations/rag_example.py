"""
RAG 시스템 사용 예시
기존 방식과 새로운 방식을 쉽게 교체하며 사용하는 방법
"""
from .rag_manager import get_rag_manager, RAGType, RAGConfig


def example_legacy_rag():
    """기존 RAG 시스템 사용 예시"""
    print("=== 기존 RAG 시스템 사용 ===")
    
    # RAG 매니저 가져오기
    manager = get_rag_manager()
    
    # 기존 RAG로 교체
    rag = manager.switch_to(RAGType.LEGACY)
    
    # 파일 처리
    # results = rag.load_and_process_file("path/to/document.pdf")
    
    # 유사도 검색
    # search_results = rag.search_similar("검색 쿼리")
    
    # 문서 추가
    # doc_id = rag.add_document("추가할 텍스트")
    
    print(f"현재 RAG 타입: {manager.get_current_type()}")
    print(f"고급 기능 지원: {manager.is_advanced_rag()}")


def example_toc_based_rag():
    """새로운 TOC 기반 RAG 시스템 사용 예시"""
    print("=== TOC 기반 RAG 시스템 사용 ===")
    
    # RAG 매니저 가져오기
    manager = get_rag_manager()
    
    # TOC 기반 RAG로 교체
    rag = manager.switch_to(RAGType.TOC_BASED)
    
    print(f"현재 RAG 타입: {manager.get_current_type()}")
    print(f"고급 기능 지원: {manager.is_advanced_rag()}")
    
    # 고급 기능 사용
    if manager.is_advanced_rag():
        advanced_rag = manager.get_advanced_rag()
        
        # 분석 결과 기반 검색
        # analysis_results = advanced_rag.search_by_analysis_result("analysis_id_123")
        
        # 조언 생성
        # advice = advanced_rag.generate_advice("analysis_id_123")
        
        # 피드백 저장
        # success = advanced_rag.save_feedback("analysis_id_123", "생성된 조언 텍스트")
        
        print("고급 RAG 기능 사용 가능")


def example_custom_config():
    """커스텀 설정으로 RAG 시스템 사용"""
    print("=== 커스텀 설정 RAG 시스템 ===")
    
    # 커스텀 설정 생성
    custom_config = RAGConfig(
        storage_type="gcp",
        chunker_type="toc_based",
        embedding_model="openai",
        vector_db_type="postgresql",
        extra_config={
            "bucket_name": "my-custom-bucket",
            "embedding_model": "text-embedding-ada-002",
            "table_name": "custom_handbook_snippet"
        }
    )
    
    # RAG 매니저 가져오기
    manager = get_rag_manager()
    
    # 커스텀 설정으로 TOC 기반 RAG 사용
    rag = manager.switch_to(RAGType.TOC_BASED, custom_config)
    
    print(f"현재 RAG 타입: {manager.get_current_type()}")
    print(f"설정: {rag.config}")


def example_rag_switching():
    """RAG 시스템 동적 교체 예시"""
    print("=== RAG 시스템 동적 교체 ===")
    
    manager = get_rag_manager()
    
    # 기존 RAG로 시작
    print("1. 기존 RAG 시스템 사용")
    legacy_rag = manager.switch_to(RAGType.LEGACY)
    print(f"   현재 타입: {manager.get_current_type()}")
    
    # 일반적인 문서 검색 수행
    # results = legacy_rag.search_similar("일반 검색 쿼리")
    
    # 고급 기능이 필요한 경우 TOC 기반으로 교체
    print("2. TOC 기반 RAG로 교체")
    toc_rag = manager.switch_to(RAGType.TOC_BASED)
    print(f"   현재 타입: {manager.get_current_type()}")
    
    # 분석 결과 기반 조언 생성
    if manager.is_advanced_rag():
        advanced_rag = manager.get_advanced_rag()
        # advice = advanced_rag.generate_advice("analysis_id")
        print("   고급 조언 생성 기능 사용")
    
    # 다시 기존 RAG로 교체
    print("3. 다시 기존 RAG로 교체")
    manager.switch_to(RAGType.LEGACY)
    print(f"   현재 타입: {manager.get_current_type()}")


if __name__ == "__main__":
    example_legacy_rag()
    print()
    example_toc_based_rag()
    print()
    example_custom_config()
    print()
    example_rag_switching()
