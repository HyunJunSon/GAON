# app/agent/Analysis/run_analysis.py
"""
✅ Analysis 모듈 실행 진입점 (DB 연동)

변경 사항:
- 기존: conversation_df를 파라미터로 직접 전달
- 변경: DB 세션을 생성하여 AnalysisGraph에 주입

🔧 수정 사항 (2025-11-07):
- LangGraph 반환 타입 처리 (dict)
- result_state.meta → result_state.get("meta", {})

사용 예시:
    from app.agent.Analysis.run_analysis import run_analysis
    
    # Cleaner 결과를 받아서 실행
    result = run_analysis(
        conv_id="uuid-string",
        user_id=1,
        conversation_df=cleaned_df
    )
"""

from app.agent.Analysis.graph_analysis import AnalysisGraph
from app.core.database_testing import SessionLocalTesting
import pandas as pd
import pprint


def run_analysis(conv_id: str = None, user_id: int = None, conversation_df: pd.DataFrame = None):
    """
    ✅ Analysis 모듈 실행 함수 (DB 연동)
    
    Args:
        conv_id: 대화 UUID (필수)
        user_id: 사용자 ID (필수)
        conversation_df: Cleaner에서 전달받은 정제된 대화 DataFrame (필수)
    
    Returns:
        dict: {
            "conv_id": str,
            "user_id": int,
            "analysis_id": str,
            "analysis_result": Dict,
            "relations": List,
            "validated": bool
        }
    
    사용 예시:
        # Cleaner 결과를 받아서 실행
        cleaner_result = run_cleaner(pk_id=1, user_id=1)
        
        analysis_result = run_analysis(
            conv_id=cleaner_result["conv_id"],
            user_id=cleaner_result["user_id"],
            conversation_df=cleaner_result["cleaned_df"]
        )
    """
    print("\n🚀 [Analysis] 실행 시작")
    print("=" * 60)
    
    # ✅ 필수 파라미터 검증
    if not conv_id:
        raise ValueError("❌ conv_id가 필요합니다!")
    
    if not user_id:
        raise ValueError("❌ user_id가 필요합니다!")
    
    if conversation_df is None or conversation_df.empty:
        raise ValueError("❌ conversation_df가 비어있습니다!")
    
    # ✅ DB 세션 생성
    db = SessionLocalTesting()
    
    try:
        # ✅ AnalysisGraph 실행
        graph = AnalysisGraph(verbose=True)
        result_state = graph.run(
            db=db,
            conversation_df=conversation_df,
            user_id=user_id,
            conv_id=conv_id
        )
        
        print("\n✅ [Analysis] 실행 완료")
        print("=" * 60)
        
        # =========================================
        # 🔧 수정: LangGraph 반환 타입 처리
        # =========================================
        # 이유: LangGraph의 pipeline.invoke()는 dict를 반환
        # - result_state.meta (X) → AttributeError
        # - result_state.get("meta", {}) (O)
        # =========================================
        
        # ✅ dict 형태로 반환됨 (LangGraph 기본 동작)
        if isinstance(result_state, dict):
            print("   🔍 [DEBUG] result_state는 dict 타입")
            result_dict = {
                "conv_id": conv_id,
                "user_id": user_id,
                "analysis_id": result_state.get("meta", {}).get("analysis_id"),  # ← 🔧 수정
                "analysis_result": result_state.get("analysis_result"),
                "relations": result_state.get("relations"),
                "family_info": result_state.get("family_info"),
                "validated": result_state.get("validated", False),
            }
        else:
            # AnalysisState 객체로 반환된 경우 (드물지만 대비)
            print("   🔍 [DEBUG] result_state는 AnalysisState 객체")
            result_dict = {
                "conv_id": conv_id,
                "user_id": user_id,
                "analysis_id": result_state.meta.get("analysis_id"),
                "analysis_result": result_state.analysis_result,
                "relations": result_state.relations,
                "family_info": result_state.family_info,
                "validated": result_state.validated,
            }
        
        return result_dict
        
    except Exception as e:
        print(f"\n❌ [Analysis] 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        # ✅ DB 세션 종료
        db.close()


# =========================================
# ✅ 단독 실행 지원
# =========================================
def main():
    """
    단독 실행 시 Analysis 단위 테스트
    
    주의: Cleaner 없이 단독 실행하려면 샘플 데이터 필요
    """
    print("\n" + "=" * 60)
    print("🧪 [Analysis 단독 실행 모드]")
    print("=" * 60)
    
    # ✅ 샘플 데이터 생성 (Cleaner 결과 대신)
    sample_df = pd.DataFrame([
        {"speaker": "1", "text": "오늘 하루 어땠어?", "timestamp": "2025-11-04 18:10:00"},
        {"speaker": "2", "text": "그냥 평범했어. 회사 일 많았어.", "timestamp": "2025-11-04 18:11:10"},
        {"speaker": "1", "text": "요즘 피곤해 보이네. 괜찮아?", "timestamp": "2025-11-04 18:12:00"},
        {"speaker": "2", "text": "응, 괜찮아. 이번 주만 지나면 나아질 거야.", "timestamp": "2025-11-04 18:13:00"},
    ])
    
    # ✅ DB에서 가장 최근 대화 조회
    db = SessionLocalTesting()
    try:
        from sqlalchemy import text
        result = db.execute(text("SELECT conv_id, user_id FROM conversation ORDER BY created_at DESC LIMIT 1;"))
        row = result.fetchone()
        
        if not row:
            raise ValueError("❌ conversation 테이블에 데이터가 없습니다!")
        
        conv_id = str(row[0])
        user_id = row[1]
        
        print(f"✅ 자동 선택된 대화: conv_id={conv_id}, user_id={user_id}")
        
    finally:
        db.close()
    
    # ✅ Analysis 실행
    result = run_analysis(
        conv_id=conv_id,
        user_id=user_id,
        conversation_df=sample_df
    )
    
    print("\n📊 [실행 결과]")
    print("-" * 60)
    pprint.pprint(result)
    
    return result


if __name__ == "__main__":
    main()