from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from typing import Dict, Any

from app.core.database import get_db
from .websocket_manager import manager
from .realtime_services import RealtimeService
from .realtime_models import MessageType, SessionStatus
from .realtime_schemas import SessionResponse


router = APIRouter(prefix="/api/conversations/realtime", tags=["realtime"])


@router.get("/sessions/family/{family_id}")
def get_family_sessions(
    family_id: int,
    db: Session = Depends(get_db)
):
    """가족의 모든 활성 세션 목록 조회"""
    service = RealtimeService(db)
    active_sessions = service.get_active_sessions_by_family(family_id)
    
    sessions = []
    for session in active_sessions:
        # 각 세션의 참여자 수 계산
        participant_count = len(manager.get_room_users(session.room_id))
        
        sessions.append({
            "id": session.id,
            "room_id": session.room_id,
            "family_id": session.family_id,
            "display_name": session.display_name,
            "created_at": session.created_at.isoformat(),
            "status": session.status.value,
            "participant_count": participant_count,
            "participants": manager.get_room_users(session.room_id)
        })
    
    return {"sessions": sessions}


@router.get("/sessions/active/{family_id}", response_model=SessionResponse)
def get_active_session(
    family_id: int,
    db: Session = Depends(get_db)
):
    """가족의 활성 세션 조회"""
    service = RealtimeService(db)
    active_sessions = service.get_active_sessions_by_family(family_id)
    
    if not active_sessions:
        raise HTTPException(status_code=404, detail="No active session found")
    
    # 가장 최근 세션 반환
    session = active_sessions[0]
    return SessionResponse(
        id=session.id,
        room_id=session.room_id,
        family_id=session.family_id,
        created_at=session.created_at,
        ended_at=session.ended_at,
        status=session.status
    )


@router.post("/sessions/{room_id}/join")
def join_session(
    room_id: str,
    db: Session = Depends(get_db)
):
    """기존 세션에 참여"""
    service = RealtimeService(db)
    session = service.get_session_by_room_id(room_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Session is not active")
    
    return SessionResponse(
        id=session.id,
        room_id=session.room_id,
        family_id=session.family_id,
        created_at=session.created_at,
        ended_at=session.ended_at,
        status=session.status
    )


@router.post("/sessions", response_model=SessionResponse)
def create_realtime_session(
    family_id: int,
    room_name: str = "가족 대화방",
    db: Session = Depends(get_db)
):
    """새로운 실시간 대화 세션 생성"""
    service = RealtimeService(db)
    session = service.create_session(family_id, room_name)
    
    return SessionResponse(
        id=session.id,
        room_id=session.room_id,
        family_id=session.family_id,
        created_at=session.created_at,
        ended_at=session.ended_at,
        status=session.status
    )


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    user_id: int,
    family_id: int,
    db: Session = Depends(get_db)
):
    """WebSocket 연결 엔드포인트"""
    service = RealtimeService(db)
    
    # 세션 존재 확인
    session = service.get_session_by_room_id(room_id)
    if not session:
        await websocket.close(code=4004, reason="Session not found")
        return
    
    # 사용자 이름 조회 (직접 psycopg2 사용)
    try:
        from app.core.config import settings
        import psycopg2
        
        database_url = settings.database_url or f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
        clean_url = database_url.replace('+psycopg2', '') if '+psycopg2' in database_url else database_url
        
        conn = psycopg2.connect(clean_url)
        cur = conn.cursor()
        cur.execute('SELECT name FROM users WHERE id = %s', (user_id,))
        result = cur.fetchone()
        user_name = result[0] if result else f"사용자{user_id}"
        cur.close()
        conn.close()
    except Exception as e:
        user_name = f"사용자{user_id}"
    
    # 연결 수락
    await manager.connect(websocket, room_id, user_id, family_id, user_name)
    
    # 입장 메시지 브로드캐스트
    join_message = {
        "type": "user_joined",
        "data": {
            "user_id": user_id,
            "user_name": user_name,
            "message": f"{user_name}님이 입장했습니다.",
            "users": manager.get_room_users(room_id)
        }
    }
    await manager.send_to_room(room_id, join_message)
    
    try:
        while True:
            # 메시지 수신
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "message":
                content = message_data.get("content", "")
                
                # DB에 메시지 저장
                db_message = service.save_message(
                    session.id, 
                    user_id, 
                    content, 
                    MessageType.TEXT
                )
                
                # 방의 모든 사용자에게 브로드캐스트
                broadcast_message = {
                    "type": "message",
                    "data": {
                        "id": db_message.id,
                        "user_id": user_id,
                        "user_name": user_name,
                        "message": content,
                        "timestamp": db_message.timestamp.isoformat()
                    }
                }
                await manager.send_to_room(room_id, broadcast_message)
                
            elif message_data.get("type") == "end_session":
                # 세션 종료
                service.end_session(room_id)
                
                # 세션 종료 메시지 브로드캐스트
                end_message = {
                    "type": "session_ended",
                    "data": {
                        "message": "대화가 종료되었습니다.",
                        "session_id": session.id
                    }
                }
                await manager.send_to_room(room_id, end_message)
                break
                
    except WebSocketDisconnect:
        # 연결 해제 처리
        manager.disconnect(websocket)
        
        # 퇴장 메시지 브로드캐스트
        user_info = manager.user_info.get(websocket)
        user_name = user_info.get("user_name", f"사용자{user_id}") if user_info else f"사용자{user_id}"
        
        leave_message = {
            "type": "user_left",
            "data": {
                "user_id": user_id,
                "user_name": user_name,
                "message": f"{user_name}님이 퇴장했습니다.",
                "users": manager.get_room_users(room_id)
            }
        }
        await manager.send_to_room(room_id, leave_message)


@router.post("/sessions/{room_id}/end")
def end_session(
    room_id: str,
    db: Session = Depends(get_db)
):
    """세션 종료 (HTTP API)"""
    service = RealtimeService(db)
    session = service.end_session(room_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session ended successfully", "session_id": session.id}


@router.post("/sessions/{room_id}/analyze")
def analyze_conversation(
    room_id: str,
    db: Session = Depends(get_db)
):
    """실시간 대화 분석"""
    service = RealtimeService(db)
    session = service.get_session_by_room_id(room_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 대화 내용을 텍스트로 변환
    conversation_text = service.export_conversation_as_text(session.id)
    
    if not conversation_text.strip():
        raise HTTPException(status_code=400, detail="No conversation to analyze")
    
    return {
        "message": "대화 분석이 시작되었습니다.",
        "conversation_text": conversation_text,
        "session_id": session.id,
        "message_count": len(service.get_session_messages(session.id))
    }
