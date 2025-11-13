# app/agent/crud.py

"""
✅ Agent 파이프라인용 CRUD 함수

목적:
- conversation, analysis_result 테이블 DB 접근 로직 중앙화
- 각 Agent 노드(Cleaner, Analysis, QA)에서 재사용

"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import pandas as pd


# =========================================
# 1️⃣ Conversation 관련 CRUD
# =========================================

def get_conversation_by_id(db: Session, conv_id: str) -> Optional[Dict[str, Any]]:
    """
    🔧 수정됨: content, family_id 제거
    """
    query = text("""
        SELECT 
            id, conv_id, title, create_date
        FROM conversation
        WHERE conv_id = :conv_id
    """)
    
    result = db.execute(query, {"conv_id": conv_id}).fetchone()
    
    if result:
        return {
            "id": result[0],
            "conv_id": str(result[1]),
            "title": result[2],
            "create_date": result[3],
        }
    return None


def get_conversation_by_pk(db: Session, pk_id: int) -> Optional[Dict[str, Any]]:

    query = text("""
        SELECT 
            id, conv_id, title, create_date
        FROM conversation
        WHERE id = :pk_id
    """)

    result = db.execute(query, {"pk_id": pk_id}).fetchone()
    
    if result:
        return {
            "id": result[0],
            "conv_id": str(result[1]),
            "title": result[2],
            "create_date": result[3],
        }
    return None



def get_conversations_by_user(db: Session, id: int, limit: int = 10) -> List[Dict[str, Any]]:

    query = text("""
        SELECT 
            id, conv_id, title, create_date
        FROM conversation
        WHERE id = :id
        ORDER BY create_date DESC
        LIMIT :limit
    """)
    
    results = db.execute(query, {"id": id, "limit": limit}).fetchall()
    
    return [
        {
            "id": row[0],
            "conv_id": str(row[1]),
            "title": row[2],
            "create_date": row[3]
        }
        for row in results
    ]


# =========================================
# 🔧 삭제됨: conversation_to_dataframe
# → RawFetcher 내부로 이동했으므로 완전 제거
# =========================================


# =========================================
# 2️⃣ User 관련 CRUD
# =========================================

def get_user_by_id(db: Session, id: int) -> Optional[Dict[str, Any]]:
    """사용자 정보 조회"""
    query = text("""
        SELECT id, name, email, create_date
        FROM users
        WHERE id = :id
    """)
    
    result = db.execute(query, {"id": id}).fetchone()
    
    if result:
        return {
            "id": result[0],
            "user_name": result[1],
            "email": result[2],
            "create_date": result[3]
        }
    return None



# =========================================
# 3️⃣ conversation_file 조회 CRUD (신규 로직)
# =========================================

def get_conversation_file_by_conv_id(db: Session, conv_id: str) -> Optional[Dict[str, Any]]:
    """
    🔥 conversation_file.raw_content 조회 (TO-BE 기준 핵심)
    """
    query = text("""
        SELECT 
            id, conv_id, file_type, raw_content, create_date
        FROM conversation_file
        WHERE conv_id = :conv_id
    """)

    result = db.execute(query, {"conv_id": conv_id}).fetchone()

    if result:
        return {
            "file_id": result[0],
            "conv_id": result[1],
            "file_type": result[2],
            "raw_content": result[3],
            "create_date": result[4]
        }
    return None



# =========================================
# 4️⃣ AnalysisResult 관련 CRUD
# =========================================

def save_analysis_result(
    db: Session,
    id: int,
    conv_id: str,
    summary: str,
    style_analysis: Dict[str, Any],
    statistics: Optional[Dict[str, Any]] = None,
    score: float = 0.0,
    confidence_score: float = 0.0,
    conversation_count: int = 0,
    feedback: Optional[str] = None,
) -> Dict[str, Any]:
    """
    분석 결과 INSERT
    """
    import json
    
    analysis_id = uuid.uuid4()

    query = text("""
        INSERT INTO analysis_result (
            analysis_id, id, conv_id, summary,
            style_analysis, statistics, score, confidence_score,
            conversation_count, feedback, create_date
        ) VALUES (
            :analysis_id, :id, :conv_id, :summary,
            :style_analysis, :statistics, :score, :confidence_score,
            :conversation_count, :feedback, NOW()
        )
        RETURNING analysis_id, id, conv_id, summary, score, confidence_score
    """)
    
    result = db.execute(query, {
        "analysis_id": str(analysis_id),
        "id": id,
        "conv_id": conv_id,
        "summary": summary,
        "style_analysis": json.dumps(style_analysis, ensure_ascii=False),
        "statistics": json.dumps(statistics, ensure_ascii=False) if statistics else None,
        "score": score,
        "confidence_score": confidence_score,
        "conversation_count": conversation_count,
        "feedback": feedback,
    })
    
    db.commit()
    
    row = result.fetchone()
    return {
        "analysis_id": str(row[0]),
        "id": str(row[1]),
        "conv_id": row[2],
        "summary": row[3],
        "score": row[4],
        "confidence_score": row[5],
    }



def update_analysis_result(
    db: Session,
    conv_id: str,
    summary: Optional[str] = None,
    style_analysis: Optional[Dict[str, Any]] = None,
    statistics: Optional[Dict[str, Any]] = None,
    score: Optional[float] = None,
    confidence_score: Optional[float] = None,
    feedback: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    분석 결과 UPDATE
    """
    import json

    query_select = text("""
        SELECT summary, style_analysis, statistics, score, confidence_score, feedback
        FROM analysis_result
        WHERE conv_id = :conv_id
    """)
    
    result = db.execute(query_select, {"conv_id": conv_id}).fetchone()
    
    if not result:
        return None
    
    new_summary = summary if summary is not None else result[0]
    new_style_analysis = json.dumps(style_analysis, ensure_ascii=False) if style_analysis is not None else result[1]
    new_statistics = json.dumps(statistics, ensure_ascii=False) if statistics is not None else result[2]
    new_score = score if score is not None else result[3]
    new_confidence_score = confidence_score if confidence_score is not None else result[4]
    new_feedback = feedback if feedback is not None else result[5]
    
    query_update = text("""
        UPDATE analysis_result
        SET 
            summary = :summary,
            style_analysis = :style_analysis,
            statistics = :statistics,
            score = :score,
            confidence_score = :confidence_score,
            feedback = :feedback,
            updated_at = NOW()
        WHERE conv_id = :conv_id
        RETURNING analysis_id, id, conv_id, summary, score, confidence_score
    """)
    
    result = db.execute(query_update, {
        "conv_id": conv_id,
        "summary": new_summary,
        "style_analysis": new_style_analysis,
        "statistics": new_statistics,
        "score": new_score,
        "confidence_score": new_confidence_score,
        "feedback": new_feedback,
    })
    
    db.commit()
    
    row = result.fetchone()
    return {
        "analysis_id": str(row[0]),
        "id": int(row[1]),
        "conv_id": row[2],
        "summary": row[3],
        "score": row[4],
        "confidence_score": row[5],
    }



def get_analysis_by_conv_id(db: Session, conv_id: str) -> Optional[Dict[str, Any]]:
    """
    분석 결과 조회
    """
    query = text("""
        SELECT 
            analysis_id, id, conv_id, summary,
            style_analysis, statistics, score, confidence_score,
            conversation_count, feedback, create_date
        FROM analysis_result
        WHERE conv_id = :conv_id
    """)
    
    result = db.execute(query, {"conv_id": conv_id}).fetchone()
    
    if result:
        import json
        
        def safe_json_load(value):
            if value is None:
                return {}
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                return json.loads(value)
            return {}
        
        return {
            "analysis_id": str(result[0]),
            "id": int(result[1]),
            "conv_id": result[2],
            "summary": result[3],
            "style_analysis": safe_json_load(result[4]),
            "statistics": safe_json_load(result[5]),
            "score": result[6],
            "confidence_score": result[7],
            "conversation_count": result[8],
            "feedback": result[9],
            "create_date": result[10]
        }
    return None

