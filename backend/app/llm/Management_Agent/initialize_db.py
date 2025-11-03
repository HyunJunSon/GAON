from datetime import datetime
from sqlalchemy import create_engine, Table, Column, Integer, String, Text, DateTime, MetaData
from app.core.database import engine

def initialize_database():
    # MetaData 객체 생성
    metadata = MetaData()

    # user 테이블 정의
    user_table = Table(
        'user',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String, nullable=False),
        Column('password', String, nullable=False),
        Column('email', String, nullable=False),
        Column('create_date', DateTime, nullable=False)
    )

    # test_raw_conversation 테이블 정의
    test_raw_conversation = Table(
        'test_raw_conversation', 
        metadata,
        Column('raw_id', Integer, primary_key=True),
        Column('user_id', Integer),
        Column('text', Text, nullable=False),
        Column('emotion', String(50)),
        Column('timestamp', DateTime, nullable=False)
    )

    try:
        # 테이블 생성
        metadata.create_all(engine)
        print("테이블이 성공적으로 생성되었습니다.")

        # 테스트 데이터 삽입
        conn = engine.connect()
        
        # 테스트 사용자 데이터
        test_users = [
            {
                'id': 101,
                'name': '테스트유저1',
                'password': 'hashed_password',
                'email': 'test1@example.com',
                'create_date': datetime.now()
            },
            {
                'id': 102,
                'name': '테스트유저2',
                'password': 'hashed_password',
                'email': 'test2@example.com',
                'create_date': datetime.now()
            }
        ]

        # 사용자 데이터 삽입
        for user in test_users:
            conn.execute(user_table.insert(), user)
        print("테스트 사용자가 생성되었습니다.")
        
        # 샘플 데이터
        sample_data = [
            {
                'raw_id': 1,
                'user_id': 101,
                'text': "안녕하세요! 오늘 기분이 정말 좋네요.",
                'emotion': "happy",
                'timestamp': datetime(2025, 11, 3, 9, 0)
            },
            {
                'raw_id': 2,
                'user_id': 101,
                'text': "날씨도 좋고 모든 게 완벽해요!",
                'emotion': "happy",
                'timestamp': datetime(2025, 11, 3, 9, 5)
            },
            {
                'raw_id': 3,
                'user_id': 102,
                'text': "요즘 일이 너무 많아서 힘드네요...",
                'emotion': "sad",
                'timestamp': datetime(2025, 11, 3, 10, 0)
            },
            {
                'raw_id': 4,
                'user_id': 102,
                'text': "하지만 열심히 해보려고요.",
                'emotion': "neutral",
                'timestamp': datetime(2025, 11, 3, 10, 5)
            }
        ]

        # 대화 데이터 삽입
        for data in sample_data:
            conn.execute(test_raw_conversation.insert(), data)
        
        conn.commit()
        print("테스트 데이터가 성공적으로 삽입되었습니다.")

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    initialize_database()