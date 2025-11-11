# backend/run_migration.py
"""
✅ Agent 파이프라인용 DB Migration 실행 스크립트

목적:
- conversation 테이블 구조 수정
- Python에서 직접 SQL 실행 (psql 불필요)

사용법:
    python run_migration.py
    테스트 DB(database_testing.py) 사용
"""

import sys
import os

# ✅ 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from app.core.database_testing import engine_testing
from sqlalchemy import text


def run_migration():
    """Migration SQL 실행"""
    print("\n" + "=" * 60)
    print("🚀 [Migration] 시작")
    print("=" * 60)
    
    migration_file = os.path.join(os.path.dirname(__file__), "migration_agent.sql")
    
    if not os.path.exists(migration_file):
        print(f"❌ SQL 파일을 찾을 수 없습니다: {migration_file}")
        return
    
    with open(migration_file, "r", encoding="utf-8") as f:
        sql_content = f.read()
    
    executed = 0
    skipped = 0
    errors = 0
    
    try:
        with engine_testing.connect() as conn:  # ✅ 수정: engine → engine_testing
            # ✅ 전체 SQL을 한 번에 실행 (PostgreSQL은 이를 지원)
            print("\n[전체 SQL 실행 중...]")
            
            try:
                conn.execute(text(sql_content))
                conn.commit()
                print("✅ Migration 완료!")
                executed = 1
                
            except Exception as e:
                error_str = str(e).lower()
                
                if any(x in error_str for x in [
                    "already exists",
                    "duplicate",
                    "does not exist"
                ]):
                    print(f"⚠️  일부 항목 스킵: {str(e)[:200]}")
                    skipped = 1
                else:
                    print(f"❌ 에러: {e}")
                    errors = 1
        
        print("\n" + "=" * 60)
        print(f"✅ [Migration] 처리 완료")
        print(f"   실행: {executed}, 스킵: {skipped}, 에러: {errors}")
        print("=" * 60)
        
        verify_migration()
        
    except Exception as e:
        print(f"\n❌ Migration 실패: {e}")
        import traceback
        traceback.print_exc()


def verify_migration():
    """
    Migration 결과 확인
    """
    print("\n📊 [Verification] 테이블 구조 확인")
    print("-" * 60)
    
    # ✅ conversation 테이블 컬럼 확인
    verify_query = """
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_name = 'conversation' 
    ORDER BY ordinal_position;
    """
    
    try:
        with engine_testing.connect() as conn:  # ✅ 수정: engine → engine_testing
            result = conn.execute(text(verify_query))
            rows = result.fetchall()
            
            print("\n✅ conversation 테이블 컬럼:")
            for row in rows:
                nullable = "NULL" if row[2] == "YES" else "NOT NULL"
                print(f"  - {row[0]:20s} {row[1]:20s} {nullable}")
            
            # ✅ 데이터 개수 확인
            count_query = "SELECT COUNT(*) FROM conversation;"
            result = conn.execute(text(count_query))
            count = result.scalar()
            print(f"\n📈 conversation 테이블 데이터 개수: {count}개")
            
    except Exception as e:
        print(f"⚠️  확인 중 에러: {e}")


if __name__ == "__main__":
    print("\n⚠️  주의: 이 작업은 DB 구조를 변경합니다!")
    print("계속하시겠습니까? (y/n): ", end="")
    
    response = input().strip().lower()
    if response == "y":
        run_migration()
    else:
        print("❌ 취소되었습니다.")