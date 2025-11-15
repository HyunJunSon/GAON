#!/usr/bin/env python3
"""
리팩토링된 Legacy RAG 시스템 테스트
"""
import os
import sys
sys.path.append('/Users/hyunjunson/Project/GAON/backend')

from app.llm.rag_interface import RAGConfig
from app.llm.rag_legacy_adapter import LegacyRAGAdapter


def test_legacy_rag_initialization():
    """Legacy RAG 초기화 테스트"""
    print("=== Legacy RAG 초기화 테스트 ===")
    
    config = RAGConfig(
        storage_type="local",
        chunker_type="recursive",
        embedding_model="openai",
        chunk_size=1000,
        chunk_overlap=100
    )
    
    try:
        rag = LegacyRAGAdapter(config)
        print("✅ Legacy RAG 초기화 성공")
        print(f"   - 스토리지 타입: {rag.config.storage_type}")
        print(f"   - 청킹 타입: {rag.config.chunker_type}")
        return rag
    except Exception as e:
        print(f"❌ Legacy RAG 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_load_and_process_file(rag):
    """파일 처리 메서드 테스트 (리팩토링 후)"""
    print("\n=== 파일 처리 메서드 테스트 ===")
    
    test_path = "test_document.pdf"
    
    try:
        results = rag.load_and_process_file(test_path)
        print("✅ 파일 처리 메서드 호출 성공")
        print(f"   - 결과: {results}")
        
        # 리팩토링 후 예상 결과 검증
        if len(results) == 1 and results[0].get('status') == 'info':
            print("✅ 리팩토링 검증 성공: Cloud Functions 위임 메시지 반환")
        else:
            print("❌ 리팩토링 검증 실패: 예상과 다른 결과")
            
    except Exception as e:
        print(f"❌ 파일 처리 메서드 실패: {e}")


def test_search_similar(rag):
    """검색 기능 테스트"""
    print("\n=== 검색 기능 테스트 ===")
    
    test_query = "가족 관계 개선"
    
    try:
        results = rag.search_similar(test_query, top_k=3)
        print("✅ 검색 기능 호출 성공")
        print(f"   - 쿼리: {test_query}")
        print(f"   - 결과 수: {len(results)}")
        print(f"   - 결과 타입: {type(results)}")
        
        if results:
            print(f"   - 첫 번째 결과 타입: {type(results[0])}")
            print(f"   - 첫 번째 결과: {results[0]}")
            
    except Exception as e:
        print(f"❌ 검색 기능 실패: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 테스트 실행"""
    print("🧪 리팩토링된 Legacy RAG 시스템 테스트 시작\n")
    
    # 1. 초기화 테스트
    rag = test_legacy_rag_initialization()
    if not rag:
        return
    
    # 2. 파일 처리 테스트 (리팩토링 검증)
    test_load_and_process_file(rag)
    
    # 3. 검색 기능 테스트
    test_search_similar(rag)
    
    print("\n🎉 테스트 완료!")


if __name__ == "__main__":
    main()
