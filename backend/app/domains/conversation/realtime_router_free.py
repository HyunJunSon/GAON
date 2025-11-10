from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from typing import Dict, Any, Optional

from app.core.database import get_db
from .websocket_manager import manager
from .realtime_services import RealtimeService
from .realtime_models import MessageType, SessionStatus
from .realtime_schemas import SessionResponse


router = APIRouter(prefix="/api/conversations/realtime", tags=["realtime"])


@router.get("/sessions/public")
def get_public_sessions(db: Session = Depends(get_db)):
    """모든 공개 세션 목록 조회"""
    service = RealtimeService(db)
    active_sessions = service.get_all_active_sessions()
    
    sessions = []
    for session in active_sessions:
        participant_count = len(manager.get_room_users(session.room_id))
        
        sessions.append({
            "id": session.id,
            "room_id": session.room_id,
            "display_name": session.display_name,
            "created_at": session.created_at.isoformat(),
            "status": session.status.value,
            "participant_count": participant_count,
            "participants": manager.get_room_users(session.room_id)
        })
    
    return {"sessions": sessions}


@router.post("/sessions/create")
def create_free_session(
    room_name: str = "자유 대화방",
    db: Session = Depends(get_db)
):
    """새로운 자유 대화 세션 생성 (가족 제약 없음)"""
    service = RealtimeService(db)
    session = service.create_free_session(room_name)
    
    return {
        "id": session.id,
        "room_id": session.room_id,
        "display_name": session.display_name,
        "created_at": session.created_at.isoformat(),
        "status": session.status.value
    }


@router.get("/sessions/{room_id}")
def get_session_info(room_id: str, db: Session = Depends(get_db)):
    """세션 정보 조회"""
    service = RealtimeService(db)
    session = service.get_session_by_room_id(room_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "id": session.id,
        "room_id": session.room_id,
        "display_name": session.display_name,
        "created_at": session.created_at.isoformat(),
        "status": session.status.value,
        "participant_count": len(manager.get_room_users(room_id)),
        "participants": manager.get_room_users(room_id)
    }


@router.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    user_id: int,
    user_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """WebSocket 연결 엔드포인트 (가족 제약 없음)"""
    service = RealtimeService(db)
    
    # 세션 존재 확인 (없으면 자동 생성)
    session = service.get_session_by_room_id(room_id)
    if not session:
        session = service.create_free_session(f"대화방 {room_id}")
    
    # 사용자 이름 설정
    if not user_name:
        try:
            from app.domains.auth.user_models import User
            user = db.query(User).filter(User.id == user_id).first()
            user_name = user.name if user else f"사용자{user_id}"
        except Exception:
            user_name = f"사용자{user_id}"
    
    # 연결 수락
    await manager.connect(websocket, room_id, user_id, None, user_name)
    
    # 입장 메시지 브로드캐스트
    join_message = {
        "type": "user_joined",
        "data": {
            "user_id": user_id,
            "user_name": user_name,
            "message": f"{user_name}님이 입장했습니다.",
            "users": manager.get_room_users(room_id),
            "timestamp": session.created_at.isoformat()
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
                
            elif message_data.get("type") == "ping":
                # 연결 상태 확인용 ping
                pong_message = {
                    "type": "pong",
                    "data": {"timestamp": session.created_at.isoformat()}
                }
                await manager.send_personal_message(websocket, pong_message)
                
            elif message_data.get("type") == "end_session":
                # 세션 종료 (방장만 가능하도록 제한 가능)
                service.end_session(room_id)
                
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
                "user_name": user_name,
                "message": f"{user_name}님이 퇴장했습니다.",
                "users": manager.get_room_users(room_id)
            }
        }
        await manager.send_to_room(room_id, leave_message)
    
    except Exception as e:
        # 예외 발생 시 연결 정리
        manager.disconnect(websocket)
        error_message = {
            "type": "error",
            "data": {
                "message": "연결 중 오류가 발생했습니다.",
                "error": str(e)
            }
        }
        try:
            await manager.send_personal_message(websocket, error_message)
        except:
            pass


@router.post("/sessions/{room_id}/end")
def end_session(room_id: str, db: Session = Depends(get_db)):
    """세션 종료 (HTTP API)"""
    service = RealtimeService(db)
    session = service.end_session(room_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session ended successfully", "session_id": session.id}


@router.get("/sessions/{room_id}/messages")
def get_session_messages(room_id: str, db: Session = Depends(get_db)):
    """세션의 메시지 기록 조회"""
    service = RealtimeService(db)
    session = service.get_session_by_room_id(room_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = service.get_session_messages(session.id)
    
    return {
        "session_id": session.id,
        "room_id": room_id,
        "messages": [
            {
                "id": msg.id,
                "user_id": msg.user_id,
                "message": msg.message,
                "timestamp": msg.timestamp.isoformat(),
                "message_type": msg.message_type.value
            }
            for msg in messages
        ]
    }
