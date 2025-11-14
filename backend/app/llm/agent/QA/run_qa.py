# app/agent/QA/run_qa.py
"""
✅ QA 모듈 실행 진입점 (DB 연동)
"""

from app.llm.agent.QA.graph_qa import QAGraph
from app.core.database import SessionLocal
import pandas as pd
import pprint


def run_qa(
    analysis_result: dict = None,
    conversation_df: pd.DataFrame = None,
    id: int = None,
    conv_id: str = None,
    verbose: bool = True
):
    """QA 모듈 실행 함수"""
    if verbose:
        print("\n" + "=" * 60)
        print("🚀 [QA] 실행 시작")
        print("=" * 60)
    
    # 필수 파라미터 검증
    if not conv_id:
        raise ValueError("❌ conv_id가 필요합니다!")
    if not id:
        raise ValueError("❌ id가 필요합니다!")
    if analysis_result is None:
        raise ValueError("❌ analysis_result가 필요합니다!")
    if conversation_df is None or conversation_df.empty:
        raise ValueError("❌ conversation_df가 비어있습니다!")
    
    # DB 세션 생성
    db = SessionLocal()
    
    try:
        # QAGraph 실행
        graph = QAGraph(verbose=verbose)
        result = graph.run(
            db=db,
            conversation_df=conversation_df,
            analysis_result=analysis_result,
            id=str(id),
            conv_id=conv_id,
        )
        
        if verbose:
            print("\n" + "=" * 60)
            print("✅ [QA] 실행 완료")
            print("=" * 60)
            print("\n📊 [QA 결과]")
            print("-" * 60)
            pprint.pprint(result)
            print(f"\n✅ QA 완료: confidence={result.get('confidence', 0.0):.2f}")
            print(f"✅ QA 상태: {result.get('status')}")
        
        # =========================================
        # ✅ graph.run()이 반환한 딕셔너리를 그대로 반환
        # =========================================
        return result
        
    except Exception as e:
        print(f"\n❌ [QA] 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "status": False,
            "conv_id": conv_id,
            "id": id,
            "error": str(e),
            "confidence": 0.0,
            "reason": f"QA 실행 실패: {str(e)}",
            "final_result": None,
            "analysis_result": analysis_result,
        }
        
    finally:
        db.close()


def main():
    """단독 실행 테스트"""
    print("\n" + "=" * 60)
    print("🧪 [QA 단독 실행 모드]")
    print("=" * 60)
    
    # 샘플 데이터
    sample_df = pd.DataFrame([
        {"speaker": "1", "text": "오늘 하루 어땠어?", "timestamp": "2025-11-04 18:10:00"},
        {"speaker": "2", "text": "그냥 평범했어. 회사 일 많았어.", "timestamp": "2025-11-04 18:11:10"},
        {"speaker": "1", "text": "요즘 피곤해 보이네. 괜찮아?", "timestamp": "2025-11-04 18:12:00"},
        {"speaker": "2", "text": "응, 괜찮아. 이번 주만 지나면 나아질 거야.", "timestamp": "2025-11-04 18:13:00"},
    ])
    
    sample_analysis_result = {
        "summary": "따뜻한 가족 간 대화",
        "style_analysis": {
            "1": {
                "말투_특징_분석": "존댓말 사용, 격려하는 표현",
                "대화_성향_및_감정_표현": "긍정적, 배려심 많음",
                "주요_관심사": "상대방의 상태 걱정"
            }
        },
        "statistics": {
            "word_count": 25,
            "avg_sentence_length": 6.3,
            "unique_words": 18,
            "top_words": ["오늘", "괜찮아", "피곤", "회사", "일"]
        },
        "score": 0.62,
    }
    
    # DB에서 최근 대화 조회
    db = SessionLocal()
    try:
        from sqlalchemy import text
        result = db.execute(text("""
            SELECT id, id 
            FROM conversation 
            ORDER BY create_date DESC 
            LIMIT 1
        """))
        row = result.fetchone()
        
        if not row:
            raise ValueError("❌ conversation 테이블에 데이터가 없습니다!")
        
        conv_id = str(row[0])
        id = row[1]
        
        print(f"✅ 자동 선택된 대화: conv_id={conv_id}, id={id}")
        
    finally:
        db.close()
    
    # QA 실행
    result = run_qa(
        analysis_result=sample_analysis_result,
        conversation_df=sample_df,
        id=id,
        conv_id=conv_id,
    )
    
    print("\n📊 [실행 결과]")
    print("-" * 60)
    pprint.pprint(result)
    
    return result


if __name__ == "__main__":
    main()