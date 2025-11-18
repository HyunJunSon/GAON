"""
분석 파이프라인 실행 상태 확인
"""

import asyncio
from app.core.database import SessionLocal
from sqlalchemy import text

async def check_pipeline_status():
    """파이프라인 실행 상태 확인"""
    db = SessionLocal()
    
    try:
        # 문서 업로드 파일들 확인
        result = db.execute(text('''
            SELECT cf.conv_id, cf.original_filename, cf.processing_status, 
                   c.title, c.create_date
            FROM conversation_file cf
            JOIN conversation c ON cf.conv_id = c.conv_id
            WHERE cf.original_filename LIKE '%.txt'
            ORDER BY cf.upload_date DESC 
            LIMIT 5
        ''')).fetchall()
        
        print("=== 문서 업로드 파일 상태 ===")
        for row in result:
            conv_id = row[0]
            filename = row[1]
            status = row[2]
            title = row[3]
            create_date = row[4]
            
            print(f"\n파일: {filename}")
            print(f"상태: {status}")
            print(f"생성일: {create_date}")
            
            # 분석 결과 확인
            analysis = db.execute(text('''
                SELECT analysis_id, score, confidence_score, create_date
                FROM analysis_result WHERE conv_id = :conv_id
            '''), {'conv_id': conv_id}).fetchone()
            
            if analysis:
                print(f"✅ 분석 완료: 점수={analysis[1]}, 분석일={analysis[3]}")
            else:
                print("❌ 분석 결과 없음")
                
                # 백그라운드 태스크 실행 테스트
                print("🔄 분석 파이프라인 수동 실행 테스트...")
                try:
                    from app.domains.conversation.router import run_agent_pipeline_async
                    result = await run_agent_pipeline_async(str(conv_id), 1)
                    print(f"파이프라인 실행 결과: {result}")
                except Exception as e:
                    print(f"파이프라인 실행 실패: {str(e)}")
                
                break  # 첫 번째 미분석 파일만 테스트
    
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(check_pipeline_status())
