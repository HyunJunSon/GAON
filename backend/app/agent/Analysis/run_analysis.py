# ===============================================
# app/agent/Analysis/run_analysis.py  (FINAL)
# ===============================================

from app.agent.Analysis.graph_analysis import AnalysisGraph
from app.core.database import SessionLocal
from sqlalchemy import text
import pprint
from dotenv import load_dotenv
load_dotenv()


# ============================================================
# 🔵 run_analysis (Clean 단계 없이 Analysis만 실행)
# ============================================================
def run_analysis(
    conv_id: str,
    speaker_segments,
    user_id: int,
    user_gender: str,
    user_age: int,
    user_name: str,
    user_speaker_label: str,
    other_speaker_label: str,
    other_display_name: str,
):

    print("\n🚀 [Analysis] 실행 시작")
    print("=" * 60)

    if not conv_id:
        raise ValueError("❌ conv_id가 필요합니다!")

    if not speaker_segments:
        raise ValueError("❌ speaker_segments가 비어 있습니다!")

    db = SessionLocal()

    try:
        graph = AnalysisGraph(verbose=True)

        state = graph.run(
            db=db,
            conv_id=conv_id,
            speaker_segments=speaker_segments,
            user_id=user_id,
            user_gender=user_gender,
            user_age=user_age,
            user_name=user_name,
            user_speaker_label=user_speaker_label,
            other_speaker_label=other_speaker_label,
            other_display_name=other_display_name,
        )

        print(">>> DEBUG: type(graph.run return) =", type(state))
        print(">>> DEBUG: graph.run return =", state)

        print("\n✅ [Analysis] 실행 완료")
        print("=" * 60)

        return {
            "conv_id": conv_id,
            "user_id": user_id,
            "analysis_id": state.get("analysis_id"),
            "summary": state.get("summary"),
            "style_analysis": state.get("style_analysis"),
            "statistics": state.get("statistics"),
            "temperature_score": state.get("temperature_score"),
            "validated": state.get("validated", True),
        }


    except Exception as e:
        print(f"\n❌ [Analysis] 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        db.close()



# ============================================================
# 🧪 단독 실행 (Cleaner 없이 테스트)
# ============================================================
def main():
    print("\n" + "=" * 60)
    print("🧪 [Analysis 단독 실행 모드 - Cleaner 없이 Test]")
    print("=" * 60)

    db = SessionLocal()

    try:
        row = db.execute(
            text("SELECT conv_id FROM conversation ORDER BY create_date DESC LIMIT 1;")
        ).fetchone()

        if not row:
            raise ValueError("❌ conversation 테이블에 데이터가 없습니다!")

        conv_id = str(row[0])
        print(f"📌 conv_id={conv_id}")

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
                "emotional_deviation": 50.5,
            }
        ]

        user_id = 1
        user_gender = "female"
        user_age = 26
        user_name = "테스트유저"
        user_speaker_label = "SPEAKER_0A"
        other_speaker_label = "SPEAKER_0B"
        other_display_name = "상대방"

    finally:
        db.close()

    result = run_analysis(
        conv_id=conv_id,
        speaker_segments=sample_segments,
        user_id=user_id,
        user_gender=user_gender,
        user_age=user_age,
        user_name=user_name,
        user_speaker_label=user_speaker_label,
        other_speaker_label=other_speaker_label,
        other_display_name=other_display_name,
    )

    print("\n📊 [실행 결과]")

    print("-" * 60)
    pprint.pprint(result)

    return result


if __name__ == "__main__":
    main()
