# ===============================================
# app/agent/Analysis/run_analysis.py  (FINAL)
# ===============================================

"""
✅ Analysis 모듈 실행 진입점 (Cleaner → Analysis 연결)
- Cleaner 결과에서 받은 speaker_segments, user_id, 성별·나이를 직접 사용
- conversation_df는 더 이상 필요 없음
"""

from app.agent.Analysis.graph_analysis import AnalysisGraph
from app.core.database import SessionLocal
from sqlalchemy import text
import pprint
from dotenv import load_dotenv
load_dotenv()


# ============================================================
# 🔵 NEW — run_analysis (최신 구조 완전 반영)
# ============================================================
def run_analysis(
    conv_id: str,
    speaker_segments,
    user_id: int,
    user_gender: str,
    user_age: int,
):
    """
    Args:
        conv_id (str): 대화 UUID
        speaker_segments (list): Cleaner의 segment-level 전체 JSON
        user_id (int): 실제 사용자 ID
        user_gender (str): 사용자 성별
        user_age (int): 사용자 나이

    Returns:
        dict:
            {
                conv_id,
                user_id,
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

    if not speaker_segments or len(speaker_segments) == 0:
        raise ValueError("❌ speaker_segments가 비어 있습니다!")

    if not user_id:
        raise ValueError("❌ user_id가 필요합니다!")

    # ---------------------------------------
    # 🔧 DB 세션
    # ---------------------------------------
    db = SessionLocal()

    try:
        # ---------------------------------------
        # 🔵 최신 AnalysisGraph 실행
        # ---------------------------------------
        graph = AnalysisGraph(verbose=True)

        state = graph.run(
            db=db,
            conv_id=conv_id,
            speaker_segments=speaker_segments,
            user_id=user_id,
            user_gender=user_gender,
            user_age=user_age,
        )

        print("\n✅ [Analysis] 실행 완료")
        print("=" * 60)

        # ---------------------------------------------------------
        # 🔵 결과 aggregation
        # ---------------------------------------------------------
        return {
            "conv_id": conv_id,
            "user_id": user_id,
            "analysis_id": state.meta.get("analysis_id"),
            "summary": state.summary,
            "style_analysis": state.style_analysis,
            "statistics": state.statistics,
            "temperature_score": state.temperature_score,
            "validated": state.validated,
        }

    except Exception as e:
        print(f"\n❌ [Analysis] 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        db.close()


# ============================================================
# 🧪 단독 실행용 main() (Cleaner 없이 테스트 가능)
# ============================================================
def main():
    print("\n" + "=" * 60)
    print("🧪 [Analysis 단독 실행 모드 - Cleaner 없이 Test]")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 가장 최근 conv_id 조회
        row = db.execute(
            text("SELECT conv_id FROM conversation ORDER BY create_date DESC LIMIT 1;")
        ).fetchone()

        if not row:
            raise ValueError("❌ conversation 테이블에 데이터가 없습니다!")

        conv_id = str(row[0])
        print(f"📌 conv_id={conv_id}")

        # 샘플 segment (Cleaner 없이 테스트 시 필요)
        sample_segments = [
            {
                "start": 0.0,
                "end": 1.2,
                "text": "오늘 어땠어?",
                "speaker": "SPEAKER_0A",
                "confidence": 0.9,
                "pitch_mean": 210,
                "pitch_std": 50,
                "energy": 0.1,
                "mfcc": [-200, 110, -30, 15, -20],
                "variation": 9.1,
                "emotional_deviation": 50.5
            }
        ]

        # 샘플 user metadata
        user_id = 1
        user_gender = "female"
        user_age = 26

    finally:
        db.close()

    # Analysis 실행
    result = run_analysis(
        conv_id=conv_id,
        speaker_segments=sample_segments,
        user_id=user_id,
        user_gender=user_gender,
        user_age=user_age,
    )

    print("\n📊 [실행 결과]")
    print("-" * 60)
    pprint.pprint(result)

    return result


if __name__ == "__main__":
    main()
