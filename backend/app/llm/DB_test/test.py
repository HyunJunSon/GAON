from sqlalchemy import text
from app.core.database import SessionLocal

def check_database_tables():
    """데이터베이스 테이블 정보 확인"""
    db = SessionLocal()
    try:
        # 테이블 개수 확인
        result = db.execute(text("""
            SELECT 
                table_name,
                COUNT(*) as column_count
            FROM information_schema.columns
            WHERE table_schema = 'public'
            GROUP BY table_name;
        """))
        
        print("\n=== 테이블 별 컬럼 개수 ===")
        for row in result:
            print(f"테이블: {row[0]}, 컬럼 수: {row[1]}")
            

        # conversation 테이블 상세 정보
        result = db.execute(text("""
            SELECT 
                column_name, 
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
                AND table_name = 'conversation'
            ORDER BY ordinal_position;
        """))
        
        print("\n=== conversation 테이블 상세 정보 ===")
        for row in result:
            nullable = "NULL 허용" if row[2] == 'YES' else "NULL 불가"
            print(f"컬럼: {row[0]}, 타입: {row[1]}, {nullable}")


        # ideal_answer 테이블 상세 정보
        result = db.execute(text("""
            SELECT 
                column_name, 
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
                AND table_name = 'ideal_answer'
            ORDER BY ordinal_position;
        """))
        
        print("\n=== ideal_answer 테이블 상세 정보 ===")
        for row in result:
            nullable = "NULL 허용" if row[2] == 'YES' else "NULL 불가"
            print(f"컬럼: {row[0]}, 타입: {row[1]}, {nullable}")

        # 테이블의 레코드 수 확인
        result = db.execute(text("""
            SELECT COUNT(*) FROM ideal_answer;
        """))
        count = result.scalar()
        print(f"\n=== ideal_answer 테이블 레코드 수: {count} ===")

    except Exception as e:
        print(f"에러 발생: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database_tables()
