"""
✅ Analysis 모듈 실행 진입점 (Updated: 가족 관계 및 사용자 조회 제거 버전)
"""

from app.agent.Analysis.graph_analysis import AnalysisGraph
from app.core.database import SessionLocal
import pandas as pd
import pprint


def run_analysis(conv_id: str = None, id: int = None, conversation_df: pd.DataFrame = None):
    """
    ✅ Analysis 모듈 실행 함수 (DB 연동)

    Args:
        conv_id: 대화 UUID (필수)
        id: 분석 대상 speaker ID (필수)
        conversation_df: Cleaner에서 전달받은 정제된 대화 DataFrame (필수)

    Returns:
        dict: {
            "conv_id": str,
            "id": int,
            "analysis_id": str,
            "analysis_result": Dict,
            "validated": bool
        }
    """

    print("\n🚀 [Analysis] 실행 시작")
    print("=" * 60)

    # =========================================
    # 🔧 필수 파라미터 검증
    # =========================================
    if not conv_id:
        raise ValueError("❌ conv_id가 필요합니다!")

    if not id:
        raise ValueError("❌ id(분석 대상 speaker)가 필요합니다!")

    if conversation_df is None or conversation_df.empty:
        raise ValueError("❌ conversation_df가 비어있습니다!")

    # =========================================
    # DB 세션 생성
    # =========================================
    db = SessionLocal()

    try:
        # =========================================
        # 🔧 AnalysisGraph 실행
        # =========================================
        graph = AnalysisGraph(verbose=True)
        result_state = graph.run(
            db=db,
            conversation_df=conversation_df,
            id=id,
            conv_id=conv_id
        )

        print("\n✅ [Analysis] 실행 완료")
        print("=" * 60)

        # =========================================
        # 🔧 LangGraph 반환 처리
        # =========================================
        if isinstance(result_state, dict):
            # 🔥 이 경우는 거의 발생하지 않지만 대비용
            print("   🔍 [DEBUG] result_state는 dict 타입")
            result_dict = {
                "conv_id": conv_id,
                "id": id,
                "analysis_id": result_state.get("meta", {}).get("analysis_id"),
                "analysis_result": result_state.get("analysis_result"),
                "validated": result_state.get("validated", False),
            }

        else:
            # 🔧 최신 구조에서는 항상 AnalysisState 객체가 넘어옴
            print("   🔍 [DEBUG] result_state는 AnalysisState 객체")

            result_dict = {
                "conv_id": conv_id,
                "id": id,
                "analysis_id": result_state.meta.get("analysis_id"),
                "analysis_result": result_state.analysis_result,
                "validated": result_state.validated,
            }

        return result_dict

    except Exception as e:
        print(f"\n❌ [Analysis] 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        db.close()


# =========================================
# ✅ 단독 실행 지원
# =========================================
def main():
    """
    단독 실행 시 Analysis 단위 테스트
    Cleaner 없이 단독 실행하려면 샘플 데이터 필요
    """
    print("\n" + "=" * 60)
    print("🧪 [Analysis 단독 실행 모드]")
    print("=" * 60)

    # =========================================
    # 샘플 테스트 데이터 생성
    # =========================================
    sample_df = pd.DataFrame([
        {"speaker": 1, "text": "오늘 하루 어땠어?", "timestamp": "2025-11-04 18:10:00"},
        {"speaker": 2, "text": "그냥 평범했어. 회사 일 많았어.", "timestamp": "2025-11-04 18:11:10"},
        {"speaker": 1, "text": "요즘 피곤해 보이네. 괜찮아?", "timestamp": "2025-11-04 18:12:00"},
        {"speaker": 2, "text": "응, 괜찮아. 이번 주만 지나면 나아질 거야.", "timestamp": "2025-11-04 18:13:00"},
    ])

    # =========================================
    # conv_id만 DB에서 가져옴
    # =========================================
    db = SessionLocal()
    try:
        from sqlalchemy import text
        result = db.execute(text("SELECT conv_id FROM conversation ORDER BY create_date DESC LIMIT 1;"))
        row = result.fetchone()

        if not row:
            raise ValueError("❌ conversation 테이블에 데이터가 없습니다!")

        conv_id = str(row[0])
        id = 1   # 🔧 테스트 시 분석 대상 speaker는 직접 지정 (예: 1번 화자)

        print(f"✅ 자동 선택된 대화: conv_id={conv_id}, 분석대상ID={id}")

    finally:
        db.close()

    # =========================================
    # Analysis 실행
    # =========================================
    result = run_analysis(
        conv_id=conv_id,
        id=id,
        conversation_df=sample_df
    )

    print("\n📊 [실행 결과]")
    print("-" * 60)
    pprint.pprint(result)

    return result


if __name__ == "__main__":
    main()
