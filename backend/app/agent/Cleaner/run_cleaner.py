# ===============================================================
# app/agent/Cleaner/run_cleaner.py  (FIXED VERSION)
# ===============================================================

from app.agent.Cleaner.graph_cleaner import CleanerGraph
from app.core.database import SessionLocal
from sqlalchemy import text
import traceback


def run_cleaner(conv_id: str = None):
    print("\n🚀 [Cleaner] 실행 시작")
    print("=" * 60)

    db = SessionLocal()

    try:
        # ======================================================
        # conv_id 미입력 → 최신 대화 자동 선택
        # ======================================================
        if not conv_id:
            print("⚠️ conv_id 없음 → 최근 대화 자동 조회")
            result = db.execute(
                text("SELECT conv_id FROM conversation ORDER BY create_date DESC LIMIT 1;")
            ).fetchone()

            if not result:
                raise ValueError("❌ conversation 테이블에 데이터가 없습니다!")

            conv_id = str(result[0])
            print(f"✅ 자동 선택된 conv_id={conv_id}")

        # ======================================================
        # CleanerGraph 실행
        # ======================================================
        cg = CleanerGraph(verbose=True)
        cleaner_result = cg.run(
            db=db,
            conv_id=conv_id,
        )

        print("\n✅ [Cleaner] 실행 완료")
        print("=" * 60)

        # ======================================================
        # cleaner_result dict 반환 그대로 활용
        # ======================================================
        return {
            "conv_id": conv_id,
            "cleaner_output": cleaner_result,
        }

    except Exception as e:
        print(f"\n❌ [Cleaner] 실행 실패: {e}")
        traceback.print_exc()
        raise

    finally:
        db.close()



# ===============================================================
# 단독 실행
# ===============================================================
def main():
    print("\n" + "=" * 60)
    print("🧪 [Cleaner 단독 실행 모드]")
    print("=" * 60)

    result = run_cleaner()

    print("\n📊 [실행 결과]")
    print("-" * 60)
    print(f"conv_id: {result['conv_id']}")

    issues = result["cleaner_output"].get("issues") or []
    print(f"issues: {issues}")

    # =======================================================
    # 🔥 speaker_segments 출력 시 None 방어 필수
    # =======================================================
    print("\n🔍 speaker_segments (features 포함) 예시:")
    segments = result["cleaner_output"].get("speaker_segments") or []
    if len(segments) == 0:
        print("⚠️ speaker_segments가 비어있거나 None입니다.")
    else:
        for seg in segments[:3]:
            print(seg)

    # =======================================================
    # user info도 None 방어
    # =======================================================
    print("\n🧑 user info:")
    print("gender:", result["cleaner_output"].get("user_gender"))
    print("age:", result["cleaner_output"].get("user_age"))

    return result


if __name__ == "__main__":
    main()
