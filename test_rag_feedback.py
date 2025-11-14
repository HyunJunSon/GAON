#!/usr/bin/env python3
"""
RAG 기반 피드백 생성기 테스트
"""
import sys
import os
sys.path.append('/Users/hyunjunson/Project/GAON/backend')

from app.llm.agent.QA.nodes import RAGFeedbackGenerator

def test_rag_feedback():
    """RAG 피드백 생성 테스트"""
    
    # 테스트용 분석 결과 데이터
    test_analysis_result = {
        "summary": """
        이 대화는 부모와 자녀 간의 학업 관련 대화입니다. 
        부모는 자녀의 성적에 대해 걱정을 표현하고 있으며, 
        자녀는 방어적인 태도를 보이고 있습니다. 
        대화 중 감정적인 표현이 많이 나타나며, 
        서로의 입장을 이해하려는 노력이 부족해 보입니다.
        """,
        "statistics": {
            "total_utterances": 24,
            "avg_utterance_length": 15.2,
            "emotion_distribution": {
                "긍정": 0.2,
                "부정": 0.5,
                "중립": 0.3
            }
        },
        "score": 65,
        "confidence_score": 78
    }
    
    print("🧪 RAG 피드백 생성기 테스트 시작")
    print("=" * 50)
    
    # RAG 피드백 생성기 초기화
    generator = RAGFeedbackGenerator(verbose=True)
    
    # 피드백 생성 테스트
    result = generator.generate_feedback(test_analysis_result)
    
    print("\n📊 테스트 결과:")
    print("=" * 50)
    print(f"상태: {result.get('status')}")
    print(f"RAG 사용: {result.get('rag_used')}")
    print(f"책 조언 개수: {result.get('book_advice_count')}")
    
    if result.get('status') == 'success':
        print(f"\n📚 발견된 책 조언:")
        for i, advice in enumerate(result.get('book_advice', [])):
            print(f"  {i+1}. 유사도: {advice['similarity']:.1%}")
            print(f"     내용: {advice['advice'][:100]}...")
            print()
        
        print(f"📝 생성된 피드백:")
        print("-" * 30)
        print(result.get('feedback', ''))
        
    elif result.get('status') == 'error':
        print(f"❌ 오류 발생: {result.get('error')}")
    
    print("\n✅ 테스트 완료")

if __name__ == "__main__":
    test_rag_feedback()
