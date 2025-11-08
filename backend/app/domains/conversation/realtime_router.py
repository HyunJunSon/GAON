from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from typing import Dict, Any

from app.core.database import get_db
from .websocket_manager import manager
from .realtime_services import RealtimeService
from .realtime_models import MessageType
from .realtime_schemas import SessionResponse


router = APIRouter(prefix="/api/conversations/realtime", tags=["realtime"])


@router.post("/sessions", response_model=SessionResponse)
def create_realtime_session(
    family_id: int,
    db: Session = Depends(get_db)
):
    """새로운 실시간 대화 세션 생성"""
    service = RealtimeService(db)
    session = service.create_session(family_id)
    
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
    
    # 연결 수락
    await manager.connect(websocket, room_id, user_id, family_id)
    
    # 입장 메시지 브로드캐스트
    join_message = {
        "type": "user_joined",
        "data": {
            "user_id": user_id,
            "message": f"사용자 {user_id}님이 입장했습니다.",
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
        leave_message = {
            "type": "user_left",
            "data": {
                "user_id": user_id,
                "message": f"사용자 {user_id}님이 퇴장했습니다.",
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


@router.get("/sessions/{room_id}/export")
def export_conversation(
    room_id: str,
    db: Session = Depends(get_db)
):
    """대화 내용 텍스트로 내보내기"""
    service = RealtimeService(db)
    session = service.get_session_by_room_id(room_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    conversation_text = service.export_conversation_as_text(session.id)
    
    return {
        "session_id": session.id,
        "room_id": room_id,
        "conversation_text": conversation_text,
        "message_count": len(service.get_session_messages(session.id))
    }
