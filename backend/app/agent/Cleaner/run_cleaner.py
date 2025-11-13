# app/agent/Cleaner/run_cleaner.py

"""
✅ Cleaner 모듈 실행 진입점 (DB 연동)

"""

from app.agent.Cleaner.graph_cleaner import CleanerGraph
from app.core.database import SessionLocal
from sqlalchemy import text
import traceback


def run_cleaner(conv_id: str = None):
    """
    ✅ Cleaner 모듈 실행 함수

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
        result_state = cg.run(
            db=db,
            conv_id=conv_id,
        )

        print("\n✅ [Cleaner] 실행 완료")
        print("=" * 60)

        # ======================================================
        # 🔧 결과 반환 
        # ======================================================
        return {
            "conv_id": result_state.conv_id,
            "raw_df": result_state.raw_df,                 # 원문 DF
            "inspected_df": result_state.inspected_df,     # 검사 후 DF
            "validated": result_state.validated,
            "issues": result_state.issues,
        }

    except Exception as e:
        print(f"\n❌ [Cleaner] 실행 실패: {e}")
        traceback.print_exc()
        raise

    finally:
        db.close()


# =========================================
# ✅ 단독 실행 지원
# =========================================
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
    print(f"validated: {result['validated']}")
    print(f"issues: {result['issues']}")

    # 🔧 cleaned_df 제거됨 → raw_df / inspected_df 출력
    if result["inspected_df"] is not None:
        print(f"\n🔍 inspected_df 미리보기:")
        print(result["inspected_df"].head(5))
    else:
        print("inspected_df is None")

    return result


if __name__ == "__main__":
    main()
