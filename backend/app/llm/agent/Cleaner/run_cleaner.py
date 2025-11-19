# app/agent/Cleaner/run_cleaner.py
"""
✅ Cleaner 모듈 실행 진입점 (DB 연동)
- 변경 사항:
  - pk_id 관련 로직 제거
  - conv_id(UUID) 기준으로 최근 대화 조회
  - create_date DESC 기준으로 가장 최근 데이터 자동 선택
"""

from app.llm.agent.Cleaner.graph_cleaner import CleanerGraph
from app.core.database import SessionLocal
from sqlalchemy import text
import traceback


def run_cleaner(conv_id: str = None, id: int = None):
    """
    ✅ Cleaner 모듈 실행 함수 (DB 연동)
    
    Args:
        conv_id (str): 대화 UUID (선택)
        id (int): 업로더 사용자 ID (선택)
    
    Returns:
        dict: {
            "conv_id": str,
            "cleaned_df": DataFrame,
            "id": int,
            "validated": bool,
            "issues": List[str]
        }
    """
    print("\n🚀 [Cleaner] 실행 시작")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # ✅ conv_id가 지정되지 않은 경우 → 가장 최근 대화 자동 조회
        if not conv_id:
            print("⚠️ conv_id 없음 → 최근 대화 자동 조회")
            result = db.execute(
                text("SELECT conv_id, id FROM conversation ORDER BY create_date DESC LIMIT 1;")
            )
            row = result.fetchone()
            
            if not row:
                raise ValueError("❌ conversation 테이블에 데이터가 없습니다!")
            
            conv_id = str(row[0])
            id = id or row[1]
            
            print(f"✅ 자동 선택된 대화: conv_id={conv_id}, id={id}")
        else:
            # ✅ conv_id가 지정된 경우 → 해당 대화의 id 조회
            if not id:
                print(f"⚠️ id 없음 → conv_id={conv_id}로 id 조회")
                result = db.execute(
                    text("SELECT id FROM conversation WHERE conv_id = :conv_id;"),
                    {"conv_id": conv_id}
                )
                row = result.fetchone()
                
                if not row:
                    raise ValueError(f"❌ conv_id={conv_id}에 해당하는 대화가 없습니다!")
                
                id = row[0]
                print(f"✅ 조회된 id: {id}")

        # ✅ CleanerGraph 실행
        cg = CleanerGraph(verbose=True)
        result_state = cg.run(
            db=db,
            conv_id=conv_id,
            id=str(id) if id else None
        )

        print("\n✅ [Cleaner] 실행 완료")
        print("=" * 60)

        # ✅ 결과 리턴
        return {
            "conv_id": result_state.conv_id or conv_id,
            "cleaned_df": result_state.cleaned_df,
            "id": id,
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
    단독 실행 시 Cleaner 단위 테스트
    """
    print("\n" + "=" * 60)
    print("🧪 [Cleaner 단독 실행 모드]")
    print("=" * 60)
    
    result = run_cleaner()
    
    print("\n📊 [실행 결과]")
    print("-" * 60)
    print(f"conv_id: {result['conv_id']}")
    print(f"id: {result['id']}")
    print(f"validated: {result['validated']}")
    print(f"issues: {result['issues']}")
    print(f"cleaned_df shape: {result['cleaned_df'].shape if result['cleaned_df'] is not None else 'None'}")
    
    if result['cleaned_df'] is not None:
        print("\n✅ cleaned_df 미리보기:")
        print(result['cleaned_df'].head(3))
    
    return result


if __name__ == "__main__":
    main()
