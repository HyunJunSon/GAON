from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
import psycopg2

router = APIRouter(prefix="/api/family", tags=["family"])

@router.get("/user/{user_id}")
def get_user_family(user_id: int):
    """사용자의 가족 정보 조회"""
    try:
        # settings에서 연결 정보 가져오기
        database_url = settings.database_url or f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
        clean_url = database_url.replace('+psycopg2', '') if '+psycopg2' in database_url else database_url
        
        conn = psycopg2.connect(clean_url)
        cur = conn.cursor()
        
        # 사용자 정보 조회
        cur.execute('SELECT id, name, email, family_id FROM users WHERE id = %s', (user_id,))
        user = cur.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user[3]:  # family_id
            raise HTTPException(status_code=404, detail="User has no family")
        
        # 가족 정보 조회
        cur.execute('SELECT id, name, description FROM family WHERE id = %s', (user[3],))
        family = cur.fetchone()
        
        if not family:
            raise HTTPException(status_code=404, detail="Family not found")
        
        # 가족 구성원 조회
        cur.execute('SELECT id, name, email FROM users WHERE family_id = %s', (family[0],))
        members = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return {
            "family": {
                "id": family[0],
                "name": family[1],
                "description": family[2]
            },
            "members": [
                {"id": member[0], "name": member[1], "email": member[2]}
                for member in members
            ]
        }
        
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
