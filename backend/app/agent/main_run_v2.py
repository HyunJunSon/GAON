# ============================================
# app/agent/main_run_new.py
# Cleaner → Analysis 실행 (FINAL REFACTORED)
# ============================================

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.agent.crud import get_conversation_file_by_conv_id
from app.agent.Cleaner.graph_cleaner import CleanerGraph
from app.agent.Analysis.graph_analysis import AnalysisGraph
from dotenv import load_dotenv
load_dotenv()


# ============================================
# ✔ Cleaner → Analysis 실행 함수
# ============================================
def run_cleaner_analysis(conv_id: str):
    db: Session = SessionLocal()

    # -------------------------------------------------
    # 1. DB raw row 확인
    # -------------------------------------------------
    file_row = get_conversation_file_by_conv_id(db, conv_id)
    if not file_row:
        raise RuntimeError(f"[ERROR] conv_id={conv_id} 를 찾을 수 없습니다.")

    print("\n==================== DB RAW DATA ====================")
    print("🎤 file_type:", file_row["file_type"])
    print("🎤 audio_url:", file_row["audio_url"])
    print("🎤 speaker_segments 개수:", len(file_row["speaker_segments"] or []))
    print("=====================================================")

    # -------------------------------------------------
    # 2. Cleaner 실행
    # -------------------------------------------------
    print("\n🧹 Running Cleaner...")
    cleaner = CleanerGraph(verbose=True)

    cleaner_output = cleaner.run(db=db, conv_id=conv_id)

    # dict 기반으로 가져오기
    speaker_segments = cleaner_output["speaker_segments"]
    speaker_mapping = cleaner_output["speaker_mapping"]
    user_gender = cleaner_output["user_gender"]
    user_age = cleaner_output["user_age"]

    # ⭐ Cleaner가 반환하는 값 추가로 수집
    user_name = cleaner_output.get("user_name")
    user_id_from_cleaner = cleaner_output.get("user_id")

    issues = cleaner_output["issues"]
    print("\n===== DEBUG BEFORE ANALYSIS — speaker_segments =====")
    for seg in speaker_segments[:10]:
        print(seg)
    print("====================================================")


    print("\n==================== CLEANER OUTPUT ====================")
    print("🟦 speaker_segments:", len(speaker_segments))
    print("🟦 speaker_mapping:", speaker_mapping)
    print("🟦 user_gender:", user_gender)
    print("🟦 user_age:", user_age)
    print("🟦 user_name:", user_name)
    print("🟦 issues:", issues)
    print("========================================================")

    # -------------------------------------------------
    # ⭐ 3. Analysis용 user_id & label 결정
    # -------------------------------------------------
    user_ids_map = speaker_mapping.get("user_ids", {})

    if not user_ids_map:
        raise RuntimeError("❌ Cleaner 결과에 user_ids mapping이 없습니다.")

    # SPEAKER_xxx 중 실제 user가 누구인지 (항상 하나)
    user_speaker_label = list(user_ids_map.keys())[0]      # 예: "SPEAKER_0A"
    user_id = list(user_ids_map.values())[0]               # 예: 9

    # 나머지 SPEAKER_xxx 는 상대방
    speaker_names = speaker_mapping.get("speaker_names", {})
    other_speakers = [
        spk for spk in speaker_names.keys()
        if spk != user_speaker_label
    ]

    # 예: SPEAKER_0B
    other_speaker_label = other_speakers[0] if other_speakers else None

    # 예: "친구"
    other_display_name = speaker_names.get(other_speaker_label, "상대방")

    print(f"\n👤 분석 대상 user_id={user_id}")
    print(f"⭐ user_speaker_label={user_speaker_label}")
    print(f"⭐ other_speaker_label={other_speaker_label}")
    print(f"⭐ other_display_name={other_display_name}")

    # -------------------------------------------------
    # 4. Analysis 실행
    # -------------------------------------------------
    print("\n🔎 Running Analysis...")
    analysis = AnalysisGraph(verbose=True)

    analysis_state = analysis.run(
        db=db,
        conv_id=conv_id,
        speaker_segments=speaker_segments,
        user_id=user_id,
        user_gender=user_gender,
        user_age=user_age,

        # ⭐ Cleaner에서 받은 값 전달
        user_name=user_name,

        # ⭐ 추가된 3개 인자
        user_speaker_label=user_speaker_label,
        other_speaker_label=other_speaker_label,
        other_display_name=other_display_name,
    )

    # -------------------------------------------------
    # 5. 결과 출력
    # -------------------------------------------------
    print("\n📊 [ANALYSIS RESULT]")
    result = {
        "analysis_id": analysis_state.get("analysis_id"),
        "conv_id": conv_id,
        "user_id": user_id,
        "summary": analysis_state.get("summary"),
        "statistics": analysis_state.get("statistics"),
        "style_analysis": analysis_state.get("style_analysis"),
        "temperature_score": analysis_state.get("temperature_score"),
        "validated": analysis_state.get("validated", True),
    }

    print(result)
    print("========================================================\n")

    db.close()
    return result


# ============================================
# CLI 실행
# ============================================
if __name__ == "__main__":
    TEST_CONV_ID = "7dfbcb88-e175-4233-898d-aa78bb94f970"
    run_cleaner_analysis(TEST_CONV_ID)
