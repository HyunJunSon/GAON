from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, DateTime, MetaData, text
from app.core.database import engine


def seed_users():
    metadata = MetaData()
    user_table = Table('user', metadata, Column('id', Integer, primary_key=True),
                       Column('name', String, nullable=False), Column('password', String, nullable=False),
                       Column('email', String, nullable=False), Column('create_date', DateTime, nullable=False))
    conn = engine.connect()
    try:
        # upsert logic: insert if id not exists
        users = [
            {'id': 101, 'name': '테스트유저1', 'password': 'hashed_password', 'email': 'test1@example.com', 'create_date': datetime.now()},
            {'id': 102, 'name': '테스트유저2', 'password': 'hashed_password', 'email': 'test2@example.com', 'create_date': datetime.now()},
        ]
        for u in users:
            # check exists
            exists = conn.execute(text('SELECT 1 FROM "user" WHERE id = :id'), {'id': u['id']}).fetchone()
            if not exists:
                conn.execute(user_table.insert(), u)
                print(f"Inserted user {u['id']}")
            else:
                print(f"User {u['id']} already exists")
        conn.commit()
    except Exception as e:
        print('Error seeding users:', e)
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    seed_users()
