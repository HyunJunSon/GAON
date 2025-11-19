# ============================================
# app/agent/main_run_new.py  (🆕 NEW)
# Cleaner → Analysis만 실행하는 전용 런너
# ============================================

import json
import pandas as pd
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.agent.crud import get_conversation_file_by_conv_id
from app.agent.Cleaner.graph_cleaner import CleanerGraph
from app.agent.Analysis.graph_analysis import AnalysisGraph
from dotenv import load_dotenv
load_dotenv()


# ============================================
# ✔ DataFrame 변환 함수
# ============================================
def segments_to_dataframe(segments, speaker_names, user_ids):
    rows = []

    for seg in segments:
        spk = seg["speaker"]
        text = seg["text"]

        # 1) 사용자 본인 user_id 매핑
        if spk in user_ids:
            speaker_id = user_ids[spk]   # int 그대로
        else:
            # 2) 사용자 외 다른 화자는 이름 또는 speaker label 사용
            #    (이름 우선)
            speaker_id = speaker_names.get(spk, spk)

        rows.append({
            "speaker": speaker_id,    # 숫자 or 이름
            "text": text
        })

    return pd.DataFrame(rows)



# ============================================
# ✔ 실행 함수
# ============================================
def run_cleaner_analysis(conv_id: str, user_id: int):
    db: Session = SessionLocal()

    # 1. DB에서 conversation_file 불러오기
    file_row = get_conversation_file_by_conv_id(db, conv_id)
    if not file_row:
        raise RuntimeError(f"[ERROR] conv_id={conv_id} 를 찾을 수 없습니다.")

    speaker_segments = file_row.get("speaker_segments")
    speaker_mapping = file_row.get("speaker_mapping")

    if speaker_segments is None:
        raise RuntimeError("speaker_segments 가 DB에 없습니다.")

    if speaker_mapping is None:
        speaker_mapping = {}

    # JSON 필드 파싱
    if isinstance(speaker_segments, str):
        speaker_segments = json.loads(speaker_segments)

    if isinstance(speaker_mapping, str):
        speaker_mapping = json.loads(speaker_mapping)

    # 2. segments 기반 DF 생성
    conversation_df = segments_to_dataframe(
        segments=speaker_segments,
        speaker_names=speaker_mapping.get("speaker_names", {}),
        user_ids=speaker_mapping.get("user_ids", {})
    )

    print("\n📄 [DEBUG] 생성된 conversation_df")
    print(conversation_df)

    # 3. Cleaner 실행
    print("\n🧹 Running Cleaner...")
    cleaner = CleanerGraph(verbose=True)

    cleaner_state = cleaner.run(
        db=db,
        conv_id=conv_id,
        conversation_df=conversation_df
    )

    # cleaner_state.merged_df 사용
    cleaned_df = cleaner_state.get("merged_df")

    print("\n🧼 [CLEANED DF]")
    print(cleaned_df)

    # 4. Analysis 실행
    print("\n🔎 Running Analysis...")
    analysis = AnalysisGraph(verbose=True)
    analysis_state = analysis.run(
        db=db,
        conversation_df=cleaned_df,
        audio_features=cleaner_state.get("audio_features"),
        id=user_id,
        conv_id=conv_id
    )

    print("\n📊 [ANALYSIS RESULT]")
    print({
        "analysis_id": analysis_state.meta.get("analysis_id"),
        "conv_id": conv_id,
        "id": user_id,
        "statistics": analysis_state.statistics,
        "style_analysis": analysis_state.style_analysis,
        "summary": analysis_state.summary,
        "temperature_score": analysis_state.temperature_score,
        "validated": analysis_state.validated,
    })

    return analysis_state



# ============================================
# CLI 실행
# ============================================
if __name__ == "__main__":
    TEST_CONV_ID = "7dfbcb88-e175-4233-898d-aa78bb94f970"
    TEST_USER_ID = 1

    run_cleaner_analysis(TEST_CONV_ID, TEST_USER_ID)
