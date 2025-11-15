#!/usr/bin/env python3
"""
수정된 ideal_answer 데이터로 RAG 테스트
"""
import sys
import os
sys.path.append('/Users/hyunjunson/Project/GAON/backend')

from dotenv import load_dotenv
load_dotenv('/Users/hyunjunson/Project/GAON/backend/.env')

import psycopg2

def test_updated_data():
    """수정된 데이터 확인 및 RAG 테스트"""
    
    print("🔍 수정된 ideal_answer 데이터 테스트")
    print("=" * 50)
    
    # DB 연결
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    
    try:
        cursor = conn.cursor()
        
        # 1. 데이터 구조 확인
        print("📊 데이터 구조 확인:")
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(book_id) as has_book_id,
                   COUNT(book_title) as has_book_title,
                   COUNT(l1_title) as has_l1_title,
                   COUNT(l2_title) as has_l2_title,
                   COUNT(l3_title) as has_l3_title
            FROM ideal_answer
        """)
        
        stats = cursor.fetchone()
        print(f"  전체 레코드: {stats[0]}개")
        print(f"  book_id: {stats[1]}개")
        print(f"  book_title: {stats[2]}개")
        print(f"  l1_title: {stats[3]}개")
        print(f"  l2_title: {stats[4]}개")
        print(f"  l3_title: {stats[5]}개")
        
        # 2. 샘플 데이터 확인
        print(f"\n📝 샘플 데이터:")
        cursor.execute("""
            SELECT book_title, l1_title, l2_title, l3_title, 
                   canonical_path, LEFT(embed_text, 100) as embed_sample
            FROM ideal_answer 
            WHERE l1_title IS NOT NULL 
            LIMIT 3
        """)
        
        samples = cursor.fetchall()
        for i, (book_title, l1, l2, l3, canonical_path, embed_sample) in enumerate(samples, 1):
            print(f"\n  샘플 {i}:")
            print(f"    책제목: {book_title}")
            print(f"    대제목: {l1}")
            print(f"    중제목: {l2}")
            print(f"    소제목: {l3}")
            print(f"    경로: {canonical_path}")
            print(f"    임베딩텍스트: {embed_sample}...")
        
        # 3. 대화 관련 키워드로 검색 테스트
        print(f"\n🔍 키워드 검색 테스트:")
        keywords = ['대화', '소통', '말하기', '가족']
        
        for keyword in keywords:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM ideal_answer 
                WHERE embed_text ILIKE %s OR full_text ILIKE %s
            """, (f'%{keyword}%', f'%{keyword}%'))
            
            count = cursor.fetchone()[0]
            print(f"  '{keyword}' 관련: {count}개")
        
        print(f"\n✅ 데이터 구조 정리 완료!")
        print(f"   이제 RAG 시스템에서 더 나은 검색 결과를 얻을 수 있습니다.")
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_updated_data()
