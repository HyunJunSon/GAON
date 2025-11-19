# ===============================================================
# app/agent/Cleaner/run_cleaner.py 
# ===============================================================

"""
✅ Cleaner 모듈 실행 진입점 (DB 연동)
Cleaner 최종 output = merged_df + file_type + audio_features 포함
"""

from app.agent.Cleaner.graph_cleaner import CleanerGraph
from app.core.database import SessionLocal
from sqlalchemy import text
import traceback


def run_cleaner(conv_id: str = None):
    """
    ✅ Cleaner 모듈 실행 함수
    - DB에서 conversation_file.raw_content 불러오기
    - turn/token 검사
    - text/audio 분리
    - audio면 음성 요소 추출
    - 최종 merged_df 생성
    """

    print("\n🚀 [Cleaner] 실행 시작")
    print("=" * 60)

    db = SessionLocal()

    try:
        # ======================================================
        # 🔧 conv_id 없으면 최근 conversation 자동 조회
        # ======================================================
        if not conv_id:
            print("⚠️ conv_id 없음 → 최근 대화 자동 조회")
            result = db.execute(
                text("SELECT conv_id FROM conversation ORDER BY create_date DESC LIMIT 1;")
            )
            row = result.fetchone()

            if not row:
                raise ValueError("❌ conversation 테이블에 데이터가 없습니다!")

            conv_id = str(row[0])
            print(f"✅ 자동 선택된 대화: conv_id={conv_id}")

        # ======================================================
        # 🔧 CleanerGraph 실행
        # ======================================================
        cg = CleanerGraph(verbose=True)
        state = cg.run(
            db=db,
            conv_id=conv_id,
        )

        print("\n✅ [Cleaner] 실행 완료")
        print("=" * 60)

        # ======================================================
        # 🔧 반환 값 구성
        # ======================================================
        # LangGraph 결과는 AddableValuesDict (dict 계열) 이므로, dict 처럼 다룬다
        if hasattr(state, "keys"):  # AddableValuesDict 또는 dict
            state_dict = dict(state)
        else:
            # 혹시나 CleanerState 인스턴스가 그대로 온 경우 fallback
            state_dict = {
                "file_type": getattr(state, "file_type", None),
                "raw_df": getattr(state, "raw_df", None),
                "inspected_df": getattr(state, "inspected_df", None),
                "merged_df": getattr(state, "merged_df", None),
                "audio_features": getattr(state, "audio_features", None),
                "validated": getattr(state, "validated", False),
                "issues": getattr(state, "issues", []),
            }

        # ======================================================
        # 🔧 반환 값 구성
        # ======================================================
        return {
            "conv_id": conv_id,
            "file_type": state_dict.get("file_type"),
            "raw_df": state_dict.get("raw_df"),
            "inspected_df": state_dict.get("inspected_df"),
            "merged_df": state_dict.get("merged_df"),
            "audio_features": state_dict.get("audio_features"),
            "validated": state_dict.get("validated", False),
            "issues": state_dict.get("issues", []),
        }

    except Exception as e:
        print(f"\n❌ [Cleaner] 실행 실패: {e}")
        traceback.print_exc()
        raise

    finally:
        db.close()


# ===============================================================
# 단독 실행 지원
# ===============================================================
def main():
    """
    TO-BE 구조 기준 Cleaner 단독 실행 테스트
    """
    print("\n" + "=" * 60)
    print("🧪 [Cleaner 단독 실행 모드]")
    print("=" * 60)

    result = run_cleaner()

    print("\n📊 [실행 결과]")
    print("-" * 60)
    print(f"conv_id: {result['conv_id']}")
    print(f"file_type: {result['file_type']}")
    print(f"validated: {result['validated']}")
    print(f"issues: {result['issues']}")

    if result["merged_df"] is not None:
        print("\n🔍 merged_df 미리보기:")
        print(result["merged_df"].head(5))
    else:
        print("merged_df is None")

    return result


if __name__ == "__main__":
    main()

