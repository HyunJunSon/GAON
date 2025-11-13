#!/usr/bin/env python3
"""
리팩토링된 TOC 기반 RAG 시스템 테스트
"""
import os
import sys
sys.path.append('/Users/hyunjunson/Project/GAON/backend')

from app.llm.rag_interface import RAGConfig
from app.llm.rag_toc_based import TOCBasedRAG


def test_toc_rag_initialization():
    """TOC RAG 초기화 테스트"""
    print("=== TOC RAG 초기화 테스트 ===")
    
    config = RAGConfig(
        embedding_model='text-embedding-3-small',
        chunk_size=1000,
        chunk_overlap=100,
        extra_config={
            'table_name': 'ideal_answer',
            'embedding_model': 'text-embedding-3-small'
        }
    )
    
    try:
        rag = TOCBasedRAG(config)
        print("✅ TOC RAG 초기화 성공")
        print(f"   - 테이블명: {rag.table_name}")
        print(f"   - 임베딩 모델: {rag.embedding_model}")
        return rag
    except Exception as e:
        print(f"❌ TOC RAG 초기화 실패: {e}")
        return None


def test_load_and_process_file(rag):
    """파일 처리 메서드 테스트 (리팩토링 후)"""
    print("\n=== 파일 처리 메서드 테스트 ===")
    
    test_path = "gs://test-bucket/test.pdf"
    
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
    
    test_query = "가족 관계 개선 방법"
    
    try:
        results = rag.search_similar(test_query, top_k=3)
        print("✅ 검색 기능 호출 성공")
        print(f"   - 쿼리: {test_query}")
        print(f"   - 결과 수: {len(results)}")
        
        for i, (text, score, doc_id) in enumerate(results):
            print(f"   - 결과 {i+1}: 점수={score:.3f}, ID={doc_id}")
            print(f"     텍스트: {text[:100]}...")
            
    except Exception as e:
        print(f"❌ 검색 기능 실패: {e}")


def main():
    """메인 테스트 실행"""
    print("🧪 리팩토링된 TOC 기반 RAG 시스템 테스트 시작\n")
    
    # 환경 변수 확인
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        return
    
    # 1. 초기화 테스트
    rag = test_toc_rag_initialization()
    if not rag:
        return
    
    # 2. 파일 처리 테스트 (리팩토링 검증)
    test_load_and_process_file(rag)
    
    # 3. 검색 기능 테스트
    test_search_similar(rag)
    
    print("\n🎉 테스트 완료!")


if __name__ == "__main__":
    main()
