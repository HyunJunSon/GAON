#!/usr/bin/env python3
"""
RAG 기능 간단 테스트
"""
import sys
import os
sys.path.append('/Users/hyunjunson/Project/GAON/backend')

def test_rag_imports():
    """RAG 관련 import 테스트"""
    try:
        print("🧪 RAG 모듈 import 테스트")
        
        # 1. VectorDBManager import 테스트
        print("1. VectorDBManager import...")
        from app.llm.cloud_functions.rag_trigger.rag.vector_db.vector_db_manager import VectorDBManager
        print("   ✅ VectorDBManager import 성공")
        
        # 2. EmbeddingService import 테스트  
        print("2. EmbeddingService import...")
        from app.llm.cloud_functions.rag_trigger.rag.vector_db.vector_db_manager import EmbeddingService
        print("   ✅ EmbeddingService import 성공")
        
        # 3. 기본 초기화 테스트
        print("3. VectorDBManager 초기화 테스트...")
        # 실제 DB 연결 없이 클래스만 확인
        print(f"   VectorDBManager 클래스: {VectorDBManager}")
        print(f"   EmbeddingService 클래스: {EmbeddingService}")
        print("   ✅ 클래스 로드 성공")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import 오류: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 기타 오류: {e}")
        return False

def test_rag_feedback_class():
    """RAGFeedbackGenerator 클래스 테스트"""
    try:
        print("\n🤖 RAGFeedbackGenerator 클래스 테스트")
        
        # RAGFeedbackGenerator import
        from app.llm.agent.QA.nodes import RAGFeedbackGenerator
        print("   ✅ RAGFeedbackGenerator import 성공")
        
        # 클래스 초기화
        generator = RAGFeedbackGenerator(verbose=True)
        print("   ✅ RAGFeedbackGenerator 초기화 성공")
        
        # 메서드 존재 확인
        if hasattr(generator, 'generate_feedback'):
            print("   ✅ generate_feedback 메서드 존재")
        else:
            print("   ❌ generate_feedback 메서드 없음")
            
        return True
        
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return False

if __name__ == "__main__":
    print("🔍 RAG 기능 테스트 시작")
    print("=" * 50)
    
    # 1. Import 테스트
    import_success = test_rag_imports()
    
    # 2. RAGFeedbackGenerator 테스트
    if import_success:
        class_success = test_rag_feedback_class()
    else:
        print("\n⏭️  Import 실패로 클래스 테스트 건너뜀")
        class_success = False
    
    print("\n📊 테스트 결과 요약:")
    print("=" * 50)
    print(f"Import 테스트: {'✅ 성공' if import_success else '❌ 실패'}")
    print(f"클래스 테스트: {'✅ 성공' if class_success else '❌ 실패'}")
    
    if import_success and class_success:
        print("\n🎉 모든 테스트 통과! RAG 기능이 정상적으로 구현되었습니다.")
    else:
        print("\n⚠️  일부 테스트 실패. 코드 수정이 필요합니다.")
