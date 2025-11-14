#!/usr/bin/env python3
"""
환경변수 로드하여 전체 RAG 플로우 테스트
"""
import sys
import os
sys.path.append('/Users/hyunjunson/Project/GAON/backend')

# 환경변수 로드
from dotenv import load_dotenv
load_dotenv('/Users/hyunjunson/Project/GAON/backend/.env')

from app.llm.agent.QA.nodes import RAGFeedbackGenerator

def test_full_rag_with_env():
    """환경변수 설정 후 전체 RAG 플로우 테스트"""
    
    print("🚀 RAG 전체 플로우 테스트 (환경변수 포함)")
    print("=" * 60)
    
    # 환경변수 확인
    print("🔧 환경변수 확인:")
    print(f"  DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET')[:50]}...")
    print(f"  OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
    print()
    
    # 테스트용 분석 결과 데이터
    test_analysis_result = {
        "summary": """
        부모와 청소년 자녀 간의 학업 스트레스에 관한 대화입니다. 
        자녀는 시험 준비로 인한 압박감을 호소했고, 부모는 격려하려 했지만 
        오히려 더 많은 기대를 표현하여 자녀가 부담을 느끼게 되었습니다. 
        대화 중 감정적 소통이 부족하고 서로의 입장을 충분히 이해하지 못했습니다.
        """,
        "statistics": {
            "total_utterances": 22,
            "avg_utterance_length": 14.8,
            "emotion_distribution": {
                "긍정": 0.15,
                "부정": 0.55,
                "중립": 0.30
            }
        },
        "score": 52,
        "confidence_score": 85
    }
    
    try:
        print("📊 테스트 데이터:")
        print(f"  - 주제: 학업 스트레스 대화")
        print(f"  - 분석 점수: {test_analysis_result['score']}/100")
        print(f"  - 신뢰도: {test_analysis_result['confidence_score']}/100")
        print(f"  - 부정 감정: {test_analysis_result['statistics']['emotion_distribution']['부정']:.1%}")
        print()
        
        # RAG 피드백 생성기 초기화
        generator = RAGFeedbackGenerator(verbose=True)
        
        print("🔍 RAG 검색 및 LLM 피드백 생성 시작...")
        print("-" * 50)
        
        # 실제 RAG + LLM 호출
        result = generator.generate_feedback(test_analysis_result)
        
        print("\n📋 테스트 결과:")
        print("=" * 60)
        
        if result.get('status') == 'success':
            print(f"✅ 상태: 성공")
            print(f"📚 RAG 사용 여부: {result.get('rag_used')}")
            print(f"📖 발견된 책 조언 수: {result.get('book_advice_count')}")
            
            # 발견된 책 조언 출력
            book_advice = result.get('book_advice', [])
            if book_advice:
                print(f"\n📚 발견된 전문가 조언 (70% 이상 유사도):")
                for i, advice in enumerate(book_advice):
                    print(f"\n  📖 조언 {i+1}:")
                    print(f"     유사도: {advice['similarity']:.1%}")
                    print(f"     ID: {advice['source_id']}")
                    print(f"     내용: {advice['advice'][:200]}...")
            else:
                print(f"\n📚 70% 이상 유사도의 관련 조언을 찾지 못했습니다.")
                print(f"   (벡터DB에 관련 데이터가 없거나 유사도가 낮음)")
            
            # 생성된 피드백 출력
            feedback = result.get('feedback', '')
            print(f"\n📝 생성된 피드백:")
            print(f"   길이: {len(feedback)}자")
            print("-" * 50)
            print(feedback)
            
            return True
            
        else:
            print(f"❌ 상태: 실패")
            print(f"오류: {result.get('error')}")
            return False
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_rag_with_env()
    
    print(f"\n🎯 최종 결과: {'✅ 성공' if success else '❌ 실패'}")
    if success:
        print("🎉 RAG 기반 피드백 생성 시스템이 정상 작동합니다!")
        print("   - 벡터DB 검색 완료")
        print("   - LLM 피드백 생성 완료")
        print("   - 전문가 조언 통합 완료")
    else:
        print("⚠️  시스템 점검이 필요합니다.")
        print("   - DB 연결 확인")
        print("   - API 키 확인")
        print("   - 벡터 데이터 확인")
