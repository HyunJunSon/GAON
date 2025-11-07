# app/agent/Cleaner/run_cleaner.py
"""
✅ Cleaner 모듈 실행 진입점 (DB 연동)

변경 사항:
- 기존: 샘플 데이터 사용
- 변경: DB에서 conversation 조회 후 처리

사용 예시:
    from app.agent.Cleaner.run_cleaner import run_cleaner
    
    result = run_cleaner(pk_id=1, user_id=1)
    print(result["cleaned_df"])
"""

from app.agent.Cleaner.graph_cleaner import CleanerGraph
from app.core.database_testing import SessionLocalTesting
import pprint


def run_cleaner(conv_id: str = None, pk_id: int = None, user_id: int = None):
    """
    ✅ Cleaner 모듈 실행 함수 (DB 연동)
    
    Args:
        conv_id: 대화 UUID (선택)
        pk_id: 대화 PK ID (선택, 기본값으로 사용 권장)
        user_id: 업로더 사용자 ID (선택)
    
    Returns:
        dict: {
            "conv_id": str,
            "pk_id": int,
            "cleaned_df": DataFrame,
            "user_id": int,
            "validated": bool,
            "issues": List[str]
        }
    
    사용 예시:
        # PK ID로 조회 (권장)
        result = run_cleaner(pk_id=1, user_id=1)
        
        # UUID로 조회
        result = run_cleaner(conv_id="uuid-string", user_id=1)
    """
    print("\n🚀 [Cleaner] 실행 시작")
    print("=" * 60)
    
    # ✅ DB 세션 생성
    db = SessionLocalTesting()
    
    try:
        # ✅ conv_id 또는 pk_id 확인
        if not conv_id and not pk_id:
            # 기본값: 가장 최근 대화 조회
            print("⚠️  conv_id/pk_id 없음 → 최근 대화 자동 조회")
            from sqlalchemy import text
            result = db.execute(text("SELECT id, conv_id, user_id FROM conversation ORDER BY created_at DESC LIMIT 1;"))
            row = result.fetchone()
            
            if not row:
                raise ValueError("❌ conversation 테이블에 데이터가 없습니다!")
            
            pk_id = row[0]
            conv_id = str(row[1])
            user_id = user_id or row[2]
            
            print(f"✅ 자동 선택된 대화: pk_id={pk_id}, conv_id={conv_id}")
        
        # ✅ CleanerGraph 실행
        cg = CleanerGraph(verbose=True)
        result_state = cg.run(
            db=db,
            conv_id=conv_id,
            pk_id=pk_id,
            user_id=str(user_id) if user_id else None
        )
        
        print("\n✅ [Cleaner] 실행 완료")
        print("=" * 60)
        
        # ✅ 결과 딕셔너리 구성 (Analysis 단계로 전달용)
        result_dict = {
            "conv_id": result_state.conv_id or conv_id,
            "pk_id": result_state.pk_id or pk_id,
            "cleaned_df": result_state.cleaned_df,
            "user_id": user_id,
            "validated": result_state.validated,
            "issues": result_state.issues,
        }
        
        return result_dict
        
    except Exception as e:
        print(f"\n❌ [Cleaner] 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        raise
        
    finally:
        # ✅ DB 세션 종료
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
    
    # ✅ 테스트: 가장 최근 대화로 실행
    result = run_cleaner()
    
    print("\n📊 [실행 결과]")
    print("-" * 60)
    print(f"conv_id: {result['conv_id']}")
    print(f"pk_id: {result['pk_id']}")
    print(f"user_id: {result['user_id']}")
    print(f"validated: {result['validated']}")
    print(f"issues: {result['issues']}")
    print(f"cleaned_df shape: {result['cleaned_df'].shape if result['cleaned_df'] is not None else 'None'}")
    
    if result['cleaned_df'] is not None:
        print("\n✅ cleaned_df 미리보기:")
        print(result['cleaned_df'].head(3))
    
    return result


if __name__ == "__main__":
    main()