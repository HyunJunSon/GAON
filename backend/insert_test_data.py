# backend/insert_test_data.py
"""
✅ 테스트 데이터 INSERT (users + conversation)
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from app.core.database_testing import SessionLocalTesting
from sqlalchemy import text
import uuid


def insert_test_data():
    """테스트 데이터 INSERT"""
    print("\n" + "=" * 60)
    print("🚀 [INSERT] 테스트 데이터 삽입 시작")
    print("=" * 60)
    
    db = SessionLocalTesting()
    
    try:
        # ✅ 0. users 테이블에 테스트 사용자 추가
        print("\n[0] 테스트 사용자 확인/추가 중...")
        result = db.execute(text("SELECT COUNT(*) FROM users WHERE id = 1;"))
        if result.scalar() == 0:
            db.execute(text("""
                INSERT INTO users (id, name, password, email, create_date)
                VALUES (1, '테스트사용자', 'test123', 'test@example.com', NOW())
                ON CONFLICT (id) DO NOTHING;
            """))
            db.commit()
            print("✅ 테스트 사용자 추가 완료")
        else:
            print("✅ 테스트 사용자 이미 존재")
        
        # ✅ 1. 기존 테스트 대화 삭제
        print("\n[1] 기존 테스트 데이터 삭제 중...")
        db.execute(text("DELETE FROM conversation WHERE cont_title LIKE '테스트%';"))
        db.commit()
        print("✅ 삭제 완료")
        
        # ✅ 2. 샘플 대화 1
        print("\n[2] 샘플 대화 1 삽입 중...")
        db.execute(text("""
            INSERT INTO conversation (
                conv_id, cont_title, cont_content, conv_start, conv_end,
                user_id, family_id, conv_file_id, created_at, updated_at
            ) VALUES (
                :conv_id, :title, :content, :start, :end,
                :user_id, NULL, NULL, NOW(), NOW()
            )
        """), {
            "conv_id": str(uuid.uuid4()),
            "title": "테스트 대화 - 건강 상태 및 일상 대화",
            "content": """참석자 1 00:00
최근에 건강한지 아니면 아픈 곳이 있었는지 이야기해 줄래요

참석자 2 00:06
아픈 곳 없어요.

참석자 1 00:12
최근에 다친 적 있어요.

참석자 2 00:16
네. 다친 적이 있어요.

참석자 1 00:25
언제 어디를 다쳤나요?

참석자 2 00:28
저번 주에 팔뚝에 멍이 들었는데 아직 멍자국이 있어요.

참석자 1 00:39
왜 팔뚝에 멍이 들게 되었어요?

참석자 2 00:43
복도 반대편에서 같은 반 남자애가 뛰어오는데 못 보고 부딪혔어요.

참석자 1 00:56
다친 다음 양호실이나 병원에 갔나요?

참석자 2 01:01
네. 양호실에 갔어요. 양호 선생님이 곧 멍이 사라질 거라고 말씀 주셨어요.

참석자 1 01:13
평소에 뭘 할 때가 제일 즐거워요?

참석자 2 01:18
친구들이랑 마라탕 먹고 인생 네컷 찍을 때가 즐거워요.

참석자 1 01:29
친구들이랑 자주 노나요?

참석자 2 01:32
네 자주 놀아요.

참석자 1 01:41
왜 그렇게 노는 게 즐거워요?

참석자 2 01:45
마라탕은 내가 원하는 재료를 담을 수 있어서 좋고 인생 네컷은 추억을 남길 수 있어서 좋아요.

참석자 1 01:58
최근 일주일 동안 짜증이나 화가 난 적이 있었어요.

참석자 2 02:04
네. 완전 짜증나고 화나는 일이 있었어요.

참석자 1 02:13
왜 짜증 나고 화가 났어요

참석자 2 02:17
친구들이랑 올리브영에서 틴트를 사기로 했는데 아빠가 돈을 안 줬어요.

참석자 1 02:28
그래서 혼자 틴트를 못 샀나요? 이런 일이 자주 있어요.

참석자 2 02:33
네. 일주일에 2 3번 친구들이랑 올리브영에 가는데 꼭 한 번씩 저만 못 사요.

참석자 1 02:46
그럴 때 어떻게 해야 짜증이나 화가 풀려요?

참석자 2 02:53
동생한테 용돈을 좀 달라고 해서 그 물건을 사면 괜찮아져요.""",
            "start": "2025-11-07 11:12:00",
            "end": "2025-11-07 11:31:08",
            "user_id": 1
        })
        db.commit()
        print("✅ 샘플 1 삽입 완료")
        
        # ✅ 3. 샘플 대화 2
        print("\n[3] 샘플 대화 2 삽입 중...")
        db.execute(text("""
            INSERT INTO conversation (
                conv_id, cont_title, cont_content, conv_start, conv_end,
                user_id, family_id, conv_file_id, created_at, updated_at
            ) VALUES (
                :conv_id, :title, :content, :start, :end,
                :user_id, NULL, NULL, NOW(), NOW()
            )
        """), {
            "conv_id": str(uuid.uuid4()),
            "title": "테스트 대화 - 가족 간 일상",
            "content": """참석자 1 00:00
오늘 하루 어땠어?

참석자 2 00:05
그냥 평범했어. 회사 일 좀 많았어.

참석자 1 00:12
요즘 피곤해 보이네. 괜찮아?

참석자 2 00:18
응, 괜찮아. 그냥 잠을 좀 못 잤어.

참석자 1 00:25
우리 아들 최고야! 숙제 다 했어?

참석자 2 00:30
응! 다 했어요!

참석자 1 00:35
주말에 뭐 하고 싶어?

참석자 2 00:40
놀이공원 가고 싶어요!""",
            "start": "2025-11-06 18:00:00",
            "end": "2025-11-06 18:05:00",
            "user_id": 1
        })
        db.commit()
        print("✅ 샘플 2 삽입 완료")
        
        # ✅ 4. 샘플 대화 3
        print("\n[4] 샘플 대화 3 삽입 중...")
        db.execute(text("""
            INSERT INTO conversation (
                conv_id, cont_title, cont_content, conv_start, conv_end,
                user_id, family_id, conv_file_id, created_at, updated_at
            ) VALUES (
                :conv_id, :title, :content, :start, :end,
                :user_id, NULL, NULL, NOW(), NOW()
            )
        """), {
            "conv_id": str(uuid.uuid4()),
            "title": "테스트 대화 - 친구 간 고민 상담",
            "content": """참석자 1 00:00
요즘 고민 있어?

참석자 2 00:05
응... 사실 좀 있어.

참석자 1 00:10
뭔데? 말해봐.

참석자 2 00:15
부모님이 자꾸 공부하라고만 하셔. 친구들이랑 놀 시간도 없어.

참석자 1 00:25
아... 그건 힘들겠다. 부모님한테 솔직하게 얘기해봤어?

참석자 2 00:32
아직... 뭐라고 말해야 할지 모르겠어.

참석자 1 00:40
천천히 생각해보고, 내가 도와줄 수 있는 거 있으면 말해!""",
            "start": "2025-11-05 20:00:00",
            "end": "2025-11-05 20:10:00",
            "user_id": 1
        })
        db.commit()
        print("✅ 샘플 3 삽입 완료")
        
        # ✅ 5. 결과 확인
        result = db.execute(text("SELECT COUNT(*) FROM conversation;"))
        count = result.scalar()
        print(f"\n📈 conversation 테이블 데이터: {count}개")
        
        # ✅ 6. 최근 3개 조회
        result = db.execute(text("""
            SELECT id, conv_id, cont_title, conv_start, conv_end 
            FROM conversation 
            ORDER BY created_at DESC 
            LIMIT 3;
        """))
        
        rows = result.fetchall()
        print("\n✅ 최근 삽입된 데이터:")
        for row in rows:
            print(f"  - id={row[0]}, title={row[2][:30]}...")
        
        print("\n" + "=" * 60)
        print("✅ [INSERT] 완료!")
        print("=" * 60)
            
    except Exception as e:
        print(f"❌ 삽입 실패: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    print("\n⚠️  주의: conversation 테이블에 테스트 데이터를 삽입합니다!")
    print("계속하시겠습니까? (y/n): ", end="")
    
    response = input().strip().lower()
    if response == "y":
        insert_test_data()
    else:
        print("❌ 취소되었습니다.")