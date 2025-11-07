# app/agent/crud.py
"""
✅ Agent 파이프라인용 CRUD 함수

목적:
- conversation, analysis_result 테이블 DB 접근 로직 중앙화
- 각 Agent 노드(Cleaner, Analysis, QA)에서 재사용

주요 함수:
1. get_conversation_by_id()       - Cleaner: conversation 조회
2. get_conversations_by_user()    - 사용자별 대화 목록 조회
3. save_conversation()            - Cleaner: 정제된 대화 저장 (현재는 이미 DB에 있음)
4. update_conversation()          - 대화 내용 업데이트
5. get_user_by_id()              - Analysis: 사용자 정보 조회
6. get_family_by_id()            - Analysis: 가족 정보 조회
7. save_analysis_result()        - Analysis: 분석 결과 저장 (INSERT)
8. update_analysis_result()      - QA: 분석 결과 업데이트 (UPDATE)
9. get_analysis_by_conv_id()     - 분석 결과 조회
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
    ✅ conversation 테이블에서 대화 조회 (conv_id 기준)
    
    Args:
        db: SQLAlchemy 세션
        conv_id: 대화 ID (UUID)
    
    Returns:
        대화 데이터 (Dict) 또는 None
    
    사용처:
        - Cleaner/nodes.py의 RawFetcher
        - main_run.py에서 대화 조회
    """
    query = text("""
        SELECT 
            id, conv_id, cont_title, cont_content,
            conv_start, conv_end, user_id, family_id,
            conv_file_id, created_at, updated_at
        FROM conversation
        WHERE conv_id = :conv_id
    """)
    
    result = db.execute(query, {"conv_id": conv_id}).fetchone()
    
    if result:
        return {
            "id": result[0],
            "conv_id": str(result[1]),
            "cont_title": result[2],
            "cont_content": result[3],
            "conv_start": result[4],
            "conv_end": result[5],
            "user_id": result[6],
            "family_id": result[7],
            "conv_file_id": result[8],
            "created_at": result[9],
            "updated_at": result[10],
        }
    return None


def get_conversation_by_pk(db: Session, pk_id: int) -> Optional[Dict[str, Any]]:
    """
    ✅ conversation 테이블에서 대화 조회 (PK id 기준)
    
    Args:
        db: SQLAlchemy 세션
        pk_id: Primary Key ID (INTEGER)
    
    Returns:
        대화 데이터 (Dict) 또는 None
    """
    query = text("""
        SELECT 
            id, conv_id, cont_title, cont_content,
            conv_start, conv_end, user_id, family_id,
            conv_file_id, created_at, updated_at
        FROM conversation
        WHERE id = :pk_id
    """)
    
    result = db.execute(query, {"pk_id": pk_id}).fetchone()
    
    if result:
        return {
            "id": result[0],
            "conv_id": str(result[1]),
            "cont_title": result[2],
            "cont_content": result[3],
            "conv_start": result[4],
            "conv_end": result[5],
            "user_id": result[6],
            "family_id": result[7],
            "conv_file_id": result[8],
            "created_at": result[9],
            "updated_at": result[10],
        }
    return None


def get_conversations_by_user(db: Session, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    ✅ 사용자별 대화 목록 조회
    
    Args:
        db: SQLAlchemy 세션
        user_id: 사용자 ID
        limit: 조회 개수
    
    Returns:
        대화 목록 (List[Dict])
    """
    query = text("""
        SELECT 
            id, conv_id, cont_title, cont_content,
            conv_start, conv_end, user_id, family_id,
            created_at, updated_at
        FROM conversation
        WHERE user_id = :user_id
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    
    results = db.execute(query, {"user_id": user_id, "limit": limit}).fetchall()
    
    return [
        {
            "id": row[0],
            "conv_id": str(row[1]),
            "cont_title": row[2],
            "cont_content": row[3],
            "conv_start": row[4],
            "conv_end": row[5],
            "user_id": row[6],
            "family_id": row[7],
            "created_at": row[8],
            "updated_at": row[9],
        }
        for row in results
    ]


def conversation_to_dataframe(conversation: Dict[str, Any]) -> pd.DataFrame:
    """
    ✅ conversation 데이터를 DataFrame으로 변환
    
    Args:
        conversation: get_conversation_by_id() 결과
    
    Returns:
        DataFrame (speaker, text, timestamp 컬럼)
    
    사용처:
        - Cleaner에서 LLM 처리용 DataFrame 생성
    """
    content = conversation["cont_content"]
    
    # ✅ 대화 내용 파싱 (형식: "참석자 1 00:00\n텍스트")
    lines = content.strip().split("\n")
    
    data = []
    current_speaker = None
    current_text = ""
    current_timestamp = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 화자 및 타임스탬프 감지 (예: "참석자 1 00:00")
        if line.startswith("참석자"):
            # 이전 발화 저장
            if current_speaker and current_text:
                data.append({
                    "speaker": current_speaker,
                    "text": current_text.strip(),
                    "timestamp": current_timestamp
                })
            
            # 새 화자 파싱
            parts = line.split(maxsplit=2)
            if len(parts) >= 2:
                current_speaker = parts[1]  # "1", "2", etc.
                current_timestamp = parts[2] if len(parts) == 3 else "00:00"
                current_text = ""
        else:
            # 텍스트 누적
            current_text += line + " "
    
    # 마지막 발화 저장
    if current_speaker and current_text:
        data.append({
            "speaker": current_speaker,
            "text": current_text.strip(),
            "timestamp": current_timestamp
        })
    
    return pd.DataFrame(data)


# =========================================
# 2️⃣ User & Family 관련 CRUD
# =========================================

def get_user_by_id(db: Session, user_id: int) -> Optional[Dict[str, Any]]:
    """
    ✅ users 테이블에서 사용자 정보 조회
    
    Args:
        db: SQLAlchemy 세션
        user_id: 사용자 ID
    
    Returns:
        사용자 정보 (Dict) 또는 None
    
    사용처:
        - Analysis/nodes.py의 UserFetcher
    """
    query = text("""
        SELECT id, name, email, create_date
        FROM users
        WHERE id = :user_id
    """)
    
    result = db.execute(query, {"user_id": user_id}).fetchone()
    
    if result:
        return {
            "user_id": result[0],
            "user_name": result[1],
            "email": result[2],
            "create_date": result[3],
        }
    return None


def get_family_by_id(db: Session, family_id: int) -> Optional[Dict[str, Any]]:
    """
    ✅ family 테이블에서 가족 정보 조회
    
    Args:
        db: SQLAlchemy 세션
        family_id: 가족 ID
    
    Returns:
        가족 정보 (Dict) 또는 None
    
    사용처:
        - Analysis/nodes.py의 FamilyChecker
    """
    query = text("""
        SELECT id, name, description, create_date
        FROM family
        WHERE id = :family_id
    """)
    
    result = db.execute(query, {"family_id": family_id}).fetchone()
    
    if result:
        return {
            "fam_id": result[0],
            "fam_name": result[1],
            "description": result[2],
            "create_date": result[3],
        }
    return None


# =========================================
# 3️⃣ AnalysisResult 관련 CRUD
# =========================================

def save_analysis_result(
    db: Session,
    user_id: str,
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
    ✅ analysis_result 테이블에 분석 결과 저장 (INSERT)
    
    Args:
        db: SQLAlchemy 세션
        user_id: 사용자 ID (UUID)
        conv_id: 대화 ID (UUID)
        summary: 분석 요약
        style_analysis: 스타일 분석 (JSONB)
        statistics: 통계 결과 (JSONB)
        score: 점수
        confidence_score: 신뢰도 점수
        conversation_count: 대화 수
        feedback: 피드백
    
    Returns:
        저장된 분석 결과 (Dict)
    
    사용처:
        - Analysis/nodes.py의 AnalysisSaver
    """
    analysis_id = uuid.uuid4()
    
    query = text("""
        INSERT INTO analysis_result (
            analysis_id, user_id, conv_id, summary,
            style_analysis, statistics, score, confidence_score,
            conversation_count, feedback, created_at, updated_at
        ) VALUES (
            :analysis_id, :user_id, :conv_id, :summary,
            :style_analysis, :statistics, :score, :confidence_score,
            :conversation_count, :feedback, NOW(), NOW()
        )
        RETURNING analysis_id, user_id, conv_id, summary, score, confidence_score
    """)
    
    import json
    result = db.execute(query, {
        "analysis_id": str(analysis_id),
        "user_id": user_id,
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
        "user_id": row[1],
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
    score: Optional[float] = None,
    confidence_score: Optional[float] = None,
    feedback: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    ✅ analysis_result 테이블 업데이트 (UPDATE)
    
    Args:
        db: SQLAlchemy 세션
        conv_id: 대화 ID (UUID)
        summary: 새 요약 (선택)
        style_analysis: 새 스타일 분석 (선택)
        score: 새 점수 (선택)
        confidence_score: 새 신뢰도 점수 (선택)
        feedback: 새 피드백 (선택)
    
    Returns:
        업데이트된 분석 결과 (Dict) 또는 None
    
    사용처:
        - QA/nodes.py의 AnalysisSaver (재분석 후 업데이트)
    """
    # ✅ 기존 데이터 조회
    query_select = text("""
        SELECT analysis_id, summary, style_analysis, score, confidence_score, feedback
        FROM analysis_result
        WHERE conv_id = :conv_id
    """)
    
    result = db.execute(query_select, {"conv_id": conv_id}).fetchone()
    
    if not result:
        return None
    
    # ✅ 업데이트할 값 준비
    import json
    
    new_summary = summary if summary is not None else result[1]
    new_style_analysis = json.dumps(style_analysis, ensure_ascii=False) if style_analysis is not None else result[2]
    new_score = score if score is not None else result[3]
    new_confidence_score = confidence_score if confidence_score is not None else result[4]
    new_feedback = feedback if feedback is not None else result[5]
    
    # ✅ UPDATE 실행
    query_update = text("""
        UPDATE analysis_result
        SET 
            summary = :summary,
            style_analysis = :style_analysis,
            score = :score,
            confidence_score = :confidence_score,
            feedback = :feedback,
            updated_at = NOW()
        WHERE conv_id = :conv_id
        RETURNING analysis_id, user_id, conv_id, summary, score, confidence_score
    """)
    
    result = db.execute(query_update, {
        "conv_id": conv_id,
        "summary": new_summary,
        "style_analysis": new_style_analysis,
        "score": new_score,
        "confidence_score": new_confidence_score,
        "feedback": new_feedback,
    })
    
    db.commit()
    
    row = result.fetchone()
    return {
        "analysis_id": str(row[0]),
        "user_id": row[1],
        "conv_id": row[2],
        "summary": row[3],
        "score": row[4],
        "confidence_score": row[5],
    }


def get_analysis_by_conv_id(db: Session, conv_id: str) -> Optional[Dict[str, Any]]:
    """
    ✅ analysis_result 테이블에서 분석 결과 조회
    
    Args:
        db: SQLAlchemy 세션
        conv_id: 대화 ID (UUID)
    
    Returns:
        분석 결과 (Dict) 또는 None
    """
    query = text("""
        SELECT 
            analysis_id, user_id, conv_id, summary,
            style_analysis, statistics, score, confidence_score,
            conversation_count, feedback, created_at, updated_at
        FROM analysis_result
        WHERE conv_id = :conv_id
    """)
    
    result = db.execute(query, {"conv_id": conv_id}).fetchone()
    
    if result:
        import json
        return {
            "analysis_id": str(result[0]),
            "user_id": result[1],
            "conv_id": result[2],
            "summary": result[3],
            "style_analysis": json.loads(result[4]) if result[4] else {},
            "statistics": json.loads(result[5]) if result[5] else {},
            "score": result[6],
            "confidence_score": result[7],
            "conversation_count": result[8],
            "feedback": result[9],
            "created_at": result[10],
            "updated_at": result[11],
        }
    return None