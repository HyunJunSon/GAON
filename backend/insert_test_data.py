# backend/insert_test_data.py
"""
✅ 테스트 데이터 INSERT 스크립트

목적:
- conversation 테이블에 샘플 대화 데이터 삽입
- Agent 파이프라인 테스트용

사용법:
    python insert_test_data.py
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from app.core.database_testing import engine_testing
from sqlalchemy import text


def insert_test_data():
    """테스트 데이터 INSERT"""
    print("\n" + "=" * 60)
    print("🚀 [INSERT] 테스트 데이터 삽입 시작")
    print("=" * 60)
    
    # ✅ SQL 파일 읽기
    sql_file = os.path.join(BASE_DIR, "insert_test_data.sql")
    
    if not os.path.exists(sql_file):
        print(f"❌ SQL 파일을 찾을 수 없습니다: {sql_file}")
        return
    
    with open(sql_file, "r", encoding="utf-8") as f:
        sql_content = f.read()
    
    try:
        with engine_testing.connect() as conn:
            print("\n[SQL 실행 중...]")
            conn.execute(text(sql_content))
            conn.commit()
            print("✅ 테스트 데이터 삽입 완료!")
            
            # ✅ 삽입 결과 확인
            result = conn.execute(text("SELECT COUNT(*) FROM conversation;"))
            count = result.scalar()
            print(f"📈 conversation 테이블 데이터: {count}개")
            
            # ✅ 최근 3개 데이터 조회
            result = conn.execute(text("""
                SELECT conv_id, cont_title, conv_start, conv_end 
                FROM conversation 
                ORDER BY created_at DESC 
                LIMIT 3;
            """))
            
            rows = result.fetchall()
            print("\n✅ 최근 삽입된 데이터:")
            for row in rows:
                print(f"  - {row[1][:30]}... ({row[2]} ~ {row[3]})")
                
    except Exception as e:
        print(f"❌ 삽입 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n⚠️  주의: conversation 테이블에 테스트 데이터를 삽입합니다!")
    print("계속하시겠습니까? (y/n): ", end="")
    
    response = input().strip().lower()
    if response == "y":
        insert_test_data()
    else:
        print("❌ 취소되었습니다.")