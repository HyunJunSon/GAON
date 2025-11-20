"""
✅ Agent 파이프라인용 CRUD 함수 (REFINED FINAL VERSION)

목적:
- conversation / conversation_file / users / analysis_result 테이블 DB 접근 중앙화
- Cleaner · Analysis agent에서 공통적으로 사용
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
import uuid
import json


# ============================================================
# 1️⃣ Conversation CRUD
# ============================================================

def get_conversation_by_id(db: Session, conv_id: str) -> Optional[Dict[str, Any]]:
    """
    conversation 기본 메타 조회
    """
    query = text("""
        SELECT 
            id, conv_id, title, create_date
        FROM conversation
        WHERE conv_id = :conv_id
    """)

    row = db.execute(query, {"conv_id": conv_id}).fetchone()

    if row:
        return {
            "id": row[0],
            "conv_id": str(row[1]),
            "title": row[2],
            "create_date": row[3],
        }
    return None


def get_conversation_by_pk(db: Session, pk_id: int) -> Optional[Dict[str, Any]]:
    query = text("""
        SELECT 
            id, conv_id, title, create_date
        FROM conversation
        WHERE id = :pk_id
    """)

    row = db.execute(query, {"pk_id": pk_id}).fetchone()

    if row:
        return {
            "id": row[0],
            "conv_id": str(row[1]),
            "title": row[2],
            "create_date": row[3],
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

    rows = db.execute(query, {"id": id, "limit": limit}).fetchall()

    return [
        {
            "id": r[0],
            "conv_id": str(r[1]),
            "title": r[2],
            "create_date": r[3]
        }
        for r in rows
    ]


# ============================================================
# 2️⃣ User CRUD  (gender / age 포함)
# ============================================================

def get_user_by_id(db: Session, id: int) -> Optional[Dict[str, Any]]:
    """
    Users 테이블에서 name, gender, age 조회
    DB 컬럼명은 name이지만 Python에서는 user_name으로 alias해서 전달
    """
    query = text("""
        SELECT id, name, email, gender, age, create_date
        FROM users
        WHERE id = :id
    """)

    row = db.execute(query, {"id": id}).fetchone()

    if row:
        return {
            "id": row[0],
            "user_name": row[1],     # DB의 name → Python user_name
            "email": row[2],
            "gender": row[3],
            "age": row[4],
            "create_date": row[5],
        }
    return None


# ============================================================
# 3️⃣ conversation_file (Audio/Text 공통)
# ============================================================

def get_conversation_file_by_conv_id(db: Session, conv_id: str) -> Optional[Dict[str, Any]]:
    """
    conversation_file 전체 row 조회
    - raw_content (txt/pdf 경우)
    - audio_url
    - speaker_segments (JSON)
    """
    query = text("""
        SELECT 
            id,
            conv_id,
            file_type,
            raw_content,
            audio_url,
            speaker_segments,
            speaker_mapping,
            upload_date
        FROM conversation_file
        WHERE conv_id = :conv_id
    """)

    row = db.execute(query, {"conv_id": conv_id}).fetchone()

    if row:
        return {
            "file_id": row[0],
            "conv_id": row[1],
            "file_type": row[2],
            "raw_content": row[3],
            "audio_url": row[4],
            "speaker_segments": row[5],
            "speaker_mapping": row[6],
            "upload_date": row[7]
        }

    return None


# ============================================================
# 4️⃣ analysis_result CRUD
# ============================================================

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

    query_select = text("""
        SELECT summary, style_analysis, statistics, score, confidence_score, feedback
        FROM analysis_result
        WHERE conv_id = :conv_id
    """)

    row = db.execute(query_select, {"conv_id": conv_id}).fetchone()
    if not row:
        return None

    new_summary = summary if summary is not None else row[0]
    new_style_analysis = json.dumps(style_analysis, ensure_ascii=False) if style_analysis else row[1]
    new_statistics = json.dumps(statistics, ensure_ascii=False) if statistics else row[2]
    new_score = score if score is not None else row[3]
    new_confidence_score = confidence_score if confidence_score is not None else row[4]
    new_feedback = feedback if feedback is not None else row[5]

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

    row2 = result.fetchone()
    return {
        "analysis_id": str(row2[0]),
        "id": int(row2[1]),
        "conv_id": row2[2],
        "summary": row2[3],
        "score": row2[4],
        "confidence_score": row2[5],
    }


def get_analysis_by_conv_id(db: Session, conv_id: str) -> Optional[Dict[str, Any]]:

    query = text("""
        SELECT 
            analysis_id, id, conv_id, summary,
            style_analysis, statistics, score, confidence_score,
            conversation_count, feedback, create_date
        FROM analysis_result
        WHERE conv_id = :conv_id
    """)

    row = db.execute(query, {"conv_id": conv_id}).fetchone()

    if not row:
        return None

    def safe_json_load(v):
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            return json.loads(v)
        return {}

    return {
        "analysis_id": str(row[0]),
        "id": int(row[1]),
        "conv_id": row[2],
        "summary": row[3],
        "style_analysis": safe_json_load(row[4]),
        "statistics": safe_json_load(row[5]),
        "score": row[6],
        "confidence_score": row[7],
        "conversation_count": row[8],
        "feedback": row[9],
        "create_date": row[10],
    }
