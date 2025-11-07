# app/agent/QA/run_qa.py
"""
✅ QA 모듈 실행 진입점 (DB 연동)

변경 사항:
- 기존: DB 세션 없이 실행
- 변경: DB 세션 생성하여 QAGraph에 주입

사용 예시:
    from app.agent.QA.run_qa import run_qa
    
    # Analysis 결과를 받아서 실행
    result = run_qa(
        analysis_result=analysis_result,
        conversation_df=conversation_df,
        user_id=1,
        conv_id="uuid-string"
    )
"""

from app.agent.QA.graph_qa import QAGraph
from app.core.database_testing import SessionLocalTesting
import pandas as pd
import pprint


def run_qa(
    analysis_result: dict = None,
    conversation_df: pd.DataFrame = None,
    user_id: int = None,
    conv_id: str = None
):
    """
    ✅ QA 모듈 실행 함수 (DB 연동)
    
    🔧 수정 사항:
    - DB 세션 생성 및 QAGraph에 주입
    - 필수 파라미터 검증 강화
    - dict 반환 타입 처리
    
    Args:
        analysis_result: Analysis 단계 결과 (필수)
        conversation_df: 대화 DataFrame (필수)
        user_id: 사용자 ID (필수)
        conv_id: 대화 UUID (필수)
    
    Returns:
        dict: {
            "conv_id": str,
            "user_id": int,
            "confidence": float,
            "reason": str,
            "final_result": Dict,
            "status": str
        }
    
    사용 예시:
        # Analysis 결과를 받아서 실행
        analysis_result = run_analysis(...)
        
        qa_result = run_qa(
            analysis_result=analysis_result["analysis_result"],
            conversation_df=cleaner_result["cleaned_df"],
            user_id=analysis_result["user_id"],
            conv_id=analysis_result["conv_id"]
        )
    """
    print("\n🚀 [QA] 실행 시작")
    print("=" * 60)
    
    # =========================================
    # ✅ 필수 파라미터 검증
    # =========================================
    
    if not conv_id:
        raise ValueError("❌ conv_id가 필요합니다!")
    
    if not user_id:
        raise ValueError("❌ user_id가 필요합니다!")
    
    if analysis_result is None:
        raise ValueError("❌ analysis_result가 필요합니다!")
    
    if conversation_df is None or conversation_df.empty:
        raise ValueError("❌ conversation_df가 비어있습니다!")
    
    # =========================================
    # 🔧 수정: DB 세션 생성
    # =========================================
    # 이유: QAGraph와 AnalysisSaver가 DB 접근 필요
    # =========================================
    
    db = SessionLocalTesting()
    
    try:
        # =========================================
        # ✅ QAGraph 실행
        # =========================================
        
        graph = QAGraph(verbose=True)
        result_state = graph.run(
            db=db,  # ← 🔧 DB 세션 주입
            conversation_df=conversation_df,
            analysis_result=analysis_result,
            user_id=str(user_id),
            conv_id=conv_id,
        )
        
        print("\n✅ [QA] 실행 완료")
        print("=" * 60)
        
        # =========================================
        # 🔧 수정: LangGraph 반환 타입 처리
        # =========================================
        # 이유: pipeline.invoke()는 dict 반환
        # =========================================
        
        if isinstance(result_state, dict):
            print("   🔍 [DEBUG] result_state는 dict 타입")
            result_dict = {
                "conv_id": conv_id,
                "user_id": user_id,
                "confidence": result_state.get("confidence", 0.0),
                "reason": result_state.get("reason", ""),
                "final_result": result_state.get("final_result"),
                "analysis_result": result_state.get("analysis_result"),
                "status": result_state.get("meta", {}).get("updated", False),
            }
        else:
            # QAState 객체로 반환된 경우 (드물지만 대비)
            print("   🔍 [DEBUG] result_state는 QAState 객체")
            result_dict = {
                "conv_id": conv_id,
                "user_id": user_id,
                "confidence": result_state.confidence,
                "reason": result_state.reason,
                "final_result": result_state.final_result,
                "analysis_result": result_state.analysis_result,
                "status": result_state.meta.get("updated", False),
            }
        
        return result_dict
        
    except Exception as e:
        print(f"\n❌ [QA] 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        # =========================================
        # ✅ DB 세션 종료
        # =========================================
        db.close()


# =========================================
# ✅ 단독 실행 지원
# =========================================
def main():
    """
    단독 실행 시 QA 단위 테스트
    
    주의: Analysis 없이 단독 실행하려면 샘플 데이터 필요
    """
    print("\n" + "=" * 60)
    print("🧪 [QA 단독 실행 모드]")
    print("=" * 60)
    
    # =========================================
    # ✅ 샘플 데이터 생성
    # =========================================
    
    # 대화 DataFrame
    sample_df = pd.DataFrame([
        {"speaker": "1", "text": "오늘 하루 어땠어?", "timestamp": "2025-11-04 18:10:00"},
        {"speaker": "2", "text": "그냥 평범했어. 회사 일 많았어.", "timestamp": "2025-11-04 18:11:10"},
        {"speaker": "1", "text": "요즘 피곤해 보이네. 괜찮아?", "timestamp": "2025-11-04 18:12:00"},
        {"speaker": "2", "text": "응, 괜찮아. 이번 주만 지나면 나아질 거야.", "timestamp": "2025-11-04 18:13:00"},
    ])
    
    # Analysis 결과 (Mock)
    sample_analysis_result = {
        "summary": "따뜻한 가족 간 대화",
        "style_analysis": {
            "1": {
                "말투_특징_분석": "존댓말 사용, 격려하는 표현",
                "대화_성향_및_감정_표현": "긍정적, 배려심 많음",
                "주요_관심사": "상대방의 상태 걱정"
            },
            "2": {
                "말투_특징_분석": "반말 사용, 간결한 표현",
                "대화_성향_및_감정_표현": "중립적, 솔직함",
                "주요_관심사": "업무 스트레스"
            }
        },
        "statistics": {
            "word_count": 25,
            "avg_sentence_length": 6.3,
            "unique_words": 18,
            "top_words": ["오늘", "괜찮아", "피곤", "회사", "일"]
        },
        "score": 0.62,  # ← 낮게 설정 (재분석 트리거)
    }
    
    # =========================================
    # ✅ DB에서 가장 최근 대화 조회
    # =========================================
    
    db = SessionLocalTesting()
    try:
        from sqlalchemy import text
        result = db.execute(text("""
            SELECT conv_id, user_id 
            FROM conversation 
            ORDER BY created_at DESC 
            LIMIT 1
        """))
        row = result.fetchone()
        
        if not row:
            raise ValueError("❌ conversation 테이블에 데이터가 없습니다!")
        
        conv_id = str(row[0])
        user_id = row[1]
        
        print(f"✅ 자동 선택된 대화: conv_id={conv_id}, user_id={user_id}")
        
    finally:
        db.close()
    
    # =========================================
    # ✅ QA 실행
    # =========================================
    
    result = run_qa(
        analysis_result=sample_analysis_result,
        conversation_df=sample_df,
        user_id=user_id,
        conv_id=conv_id,
    )
    
    print("\n📊 [실행 결과]")
    print("-" * 60)
    pprint.pprint(result)
    
    return result


if __name__ == "__main__":
    main()