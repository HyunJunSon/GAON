#!/usr/bin/env python3
"""
RAG 전체 플로우 실제 LLM 호출 테스트
"""
import sys
import os
sys.path.append('/Users/hyunjunson/Project/GAON/backend')

from app.llm.agent.QA.nodes import RAGFeedbackGenerator

def test_full_rag_flow():
    """실제 LLM 호출을 포함한 전체 RAG 플로우 테스트"""
    
    # 테스트용 분석 결과 데이터
    test_analysis_result = {
        "summary": """
        부모와 10대 자녀 간의 학업 성적에 관한 대화입니다. 
        부모는 자녀의 수학 성적 하락을 걱정하며 추가 학습을 제안했지만, 
        자녀는 이미 충분히 노력하고 있다며 방어적으로 반응했습니다. 
        대화 중 감정적 표현이 증가하고 서로의 관점을 이해하려는 노력이 부족했습니다.
        """,
        "statistics": {
            "total_utterances": 18,
            "avg_utterance_length": 12.5,
            "emotion_distribution": {
                "긍정": 0.1,
                "부정": 0.6,
                "중립": 0.3
            }
        },
        "score": 45,
        "confidence_score": 82
    }
    
    print("🚀 RAG 전체 플로우 실제 테스트 시작")
    print("=" * 60)
    
    try:
        # RAG 피드백 생성기 초기화
        generator = RAGFeedbackGenerator(verbose=True)
        
        print("📊 테스트 데이터:")
        print(f"  - 분석 점수: {test_analysis_result['score']}/100")
        print(f"  - 신뢰도: {test_analysis_result['confidence_score']}/100")
        print(f"  - 부정 감정 비율: {test_analysis_result['statistics']['emotion_distribution']['부정']:.1%}")
        print()
        
        # 실제 RAG + LLM 호출
        print("🔍 RAG 검색 및 LLM 피드백 생성 중...")
        result = generator.generate_feedback(test_analysis_result)
        
        print("\n📋 테스트 결과:")
        print("=" * 60)
        
        if result.get('status') == 'success':
            print(f"✅ 상태: 성공")
            print(f"📚 RAG 사용: {result.get('rag_used')}")
            print(f"📖 책 조언 개수: {result.get('book_advice_count')}")
            
            # 발견된 책 조언 출력
            book_advice = result.get('book_advice', [])
            if book_advice:
                print(f"\n📚 발견된 전문가 조언:")
                for i, advice in enumerate(book_advice):
                    print(f"  {i+1}. 유사도: {advice['similarity']:.1%}")
                    print(f"     조언: {advice['advice'][:150]}...")
                    print()
            else:
                print(f"\n📚 70% 이상 유사도의 조언을 찾지 못했습니다.")
            
            # 생성된 피드백 출력
            feedback = result.get('feedback', '')
            print(f"📝 생성된 피드백 (길이: {len(feedback)}자):")
            print("-" * 50)
            print(feedback)
            
        else:
            print(f"❌ 상태: 실패")
            print(f"오류: {result.get('error')}")
        
        print(f"\n✅ 전체 플로우 테스트 완료")
        return result.get('status') == 'success'
        
    except Exception as e:
        print(f"❌ 테스트 실행 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_rag_flow()
    
    print(f"\n🎯 최종 결과: {'✅ 성공' if success else '❌ 실패'}")
    if success:
        print("RAG 기반 피드백 생성 시스템이 정상 작동합니다!")
    else:
        print("시스템 점검이 필요합니다.")
