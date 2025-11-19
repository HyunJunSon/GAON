# ===============================================
# app/agent/Analysis/run_analysis.py
# ===============================================

"""
✅ Analysis 모듈 실행 진입점 (최신 구조 반영)
- Cleaner → Analysis 연결을 위한 단일 실행 파일
"""

from app.agent.Analysis.graph_analysis import AnalysisGraph
from app.core.database import SessionLocal
import pandas as pd
import pprint
from dotenv import load_dotenv
load_dotenv()


# ============================================================
# 🔵 NEW — run_analysis: audio_features 포함한 최신 구조
# ============================================================
def run_analysis(conv_id: str = None, id: int = None, conversation_df: pd.DataFrame = None, audio_features=None):
    """
    최신 Analysis 파이프라인 실행 함수

    Args:
        conv_id: 대화 UUID (필수)
        id: 분석 대상 speaker ID
        conversation_df: Cleaner에서 전달받은 정제된 text DF
        audio_features: Cleaner에서 추출된 segment-level audio features

    Returns:
        dict:
            {
                conv_id,
                id,
                analysis_id,
                summary,
                style_analysis,
                statistics,
                temperature_score,
                validated
            }
    """

    print("\n🚀 [Analysis] 실행 시작")
    print("=" * 60)

    # ---------------------------------------
    # 🔧 필수 파라미터 검사
    # ---------------------------------------
    if not conv_id:
        raise ValueError("❌ conv_id가 필요합니다!")

    if not id:
        raise ValueError("❌ id(분석 대상 speaker)가 필요합니다!")

    if conversation_df is None or conversation_df.empty:
        raise ValueError("❌ conversation_df가 비어있습니다!")

    if audio_features is None:
        audio_features = []

    # ---------------------------------------
    # 🔧 DB 세션
    # ---------------------------------------
    db = SessionLocal()

    try:
        # ---------------------------------------
        # 🔵 NEW — 최신 AnalysisGraph 실행
        # ---------------------------------------
        graph = AnalysisGraph(verbose=True)
        result_state = graph.run(
            db=db,
            conversation_df=conversation_df,
            audio_features=audio_features,
            id=id,
            conv_id=conv_id
        )

        print("\n✅ [Analysis] 실행 완료")
        print("=" * 60)

        # ---------------------------------------------------------
        # 🔵 NEW — LangGraph State → API Response 변환
        # ---------------------------------------------------------
        result_dict = {
            "conv_id": conv_id,
            "id": id,
            "analysis_id": result_state.meta.get("analysis_id"),
            "summary": result_state.summary,
            "style_analysis": result_state.style_analysis,
            "statistics": result_state.statistics,
            "temperature_score": result_state.temperature_score,
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



# ============================================================
# 🧪 단독 실행용 main() 함수
# ============================================================
def main():
    """
    Cleaner 없이 단독 테스트가 가능한 모드
    """
    print("\n" + "=" * 60)
    print("🧪 [Analysis 단독 실행 모드]")
    print("=" * 60)

    # ---------------------------------------
    # 🔧 샘플 텍스트 DF 생성
    # ---------------------------------------
    sample_df = pd.DataFrame([
        {"speaker": 1, "text": "오늘 하루 어땠어?"},
        {"speaker": 2, "text": "응, 그냥 평범했어."},
        {"speaker": 1, "text": "좀 피곤해 보이네?"},
    ])

    # audio_features는 빈 리스트로 테스트
    sample_audio = []

    # ---------------------------------------
    # 🔧 DB에서 가장 최근 conv_id 가져오기
    # ---------------------------------------
    db = SessionLocal()
    try:
        from sqlalchemy import text
        result = db.execute(text("SELECT conv_id FROM conversation ORDER BY create_date DESC LIMIT 1;"))
        row = result.fetchone()

        if not row:
            raise ValueError("❌ conversation 테이블에 데이터가 없습니다!")

        conv_id = str(row[0])
        id = 1

        print(f"✅ 자동 선택된 대화: conv_id={conv_id}, 분석대상ID={id}")

    finally:
        db.close()

    # ---------------------------------------
    # 🔧 Analysis 실행
    # ---------------------------------------
    result = run_analysis(
        conv_id=conv_id,
        id=id,
        conversation_df=sample_df,
        audio_features=sample_audio
    )

    print("\n📊 [실행 결과]")
    print("-" * 60)
    pprint.pprint(result)

    return result



if __name__ == "__main__":
    main()
