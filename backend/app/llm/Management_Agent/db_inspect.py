from sqlalchemy import text
from app.core.database import SessionLocal


def inspect_db():
    db = SessionLocal()
    try:
        print('\n-- users in `user` table --')
        users = db.execute(text('SELECT id, name, email FROM "user" ORDER BY id')).fetchall()
        if not users:
            print('No users found')
        else:
            for u in users:
                print(f'id={u[0]}, name={u[1]}, email={u[2]}')

        print('\n-- conversation table columns --')
        cols = db.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='conversation' ORDER BY ordinal_position")).fetchall()
        if not cols:
            print('conversation table not found')
        else:
            for c in cols:
                print(f'{c[0]}: {c[1]}')

        print('\n-- foreign key constraints referencing conversation.user_id --')
        # check foreign key constraints for conversation.user_id
        fks = db.execute(text("""
            SELECT
                tc.constraint_name, kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = 'conversation'
        """)).fetchall()
        if not fks:
            print('No foreign keys on conversation')
        else:
            for fk in fks:
                print(f'constraint={fk[0]}, column={fk[1]} -> {fk[2]}.{fk[3]}')

        # count rows in conversation
        cnt = db.execute(text('SELECT COUNT(*) FROM conversation')).scalar()
        print(f'\nconversation row count: {cnt}')

    except Exception as e:
        print('Error inspecting DB:', e)
    finally:
        db.close()

if __name__ == '__main__':
    inspect_db()
