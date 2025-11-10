from typing import Dict, List, Optional
from fastapi import WebSocket
import json
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # room_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # websocket -> user_info
        self.user_info: Dict[WebSocket, dict] = {}
        # 연결 상태 추적
        self.connection_status: Dict[WebSocket, bool] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: int, 
                     family_id: Optional[int] = None, user_name: str = None):
        """WebSocket 연결 처리"""
        try:
            await websocket.accept()
            
            if room_id not in self.active_connections:
                self.active_connections[room_id] = []
            
            self.active_connections[room_id].append(websocket)
            self.user_info[websocket] = {
                "user_id": user_id,
                "user_name": user_name or f"사용자{user_id}",
                "family_id": family_id,
                "room_id": room_id,
                "joined_at": datetime.now()
            }
            self.connection_status[websocket] = True
            
            logger.info(f"User {user_id} ({user_name}) connected to room {room_id}")
            
        except Exception as e:
            logger.error(f"Connection failed for user {user_id}: {e}")
            raise

    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결 해제 처리"""
        try:
            user_info = self.user_info.get(websocket)
            if user_info:
                room_id = user_info["room_id"]
                user_id = user_info["user_id"]
                user_name = user_info["user_name"]
                
                # 방에서 연결 제거
                if room_id in self.active_connections:
                    if websocket in self.active_connections[room_id]:
                        self.active_connections[room_id].remove(websocket)
                    
                    # 방이 비어있으면 제거
                    if not self.active_connections[room_id]:
                        del self.active_connections[room_id]
                
                # 사용자 정보 제거
                del self.user_info[websocket]
                
                # 연결 상태 제거
                if websocket in self.connection_status:
                    del self.connection_status[websocket]
                
                logger.info(f"User {user_id} ({user_name}) disconnected from room {room_id}")
                
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    async def send_to_room(self, room_id: str, message: dict):
        """방의 모든 사용자에게 메시지 전송"""
        if room_id not in self.active_connections:
            return
        
        # 연결이 끊어진 WebSocket들을 추적
        disconnected_websockets = []
        
        for connection in self.active_connections[room_id].copy():
            try:
                if self.connection_status.get(connection, False):
                    await connection.send_text(json.dumps(message, ensure_ascii=False))
                else:
                    disconnected_websockets.append(connection)
            except Exception as e:
                logger.warning(f"Failed to send message to connection: {e}")
                disconnected_websockets.append(connection)
        
        # 끊어진 연결들 정리
        for ws in disconnected_websockets:
            self.disconnect(ws)

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """개별 사용자에게 메시지 전송"""
        try:
            if self.connection_status.get(websocket, False):
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Failed to send personal message: {e}")
            self.disconnect(websocket)

    def get_room_users(self, room_id: str) -> List[dict]:
        """방의 사용자 목록 조회"""
        if room_id not in self.active_connections:
            return []
        
        users = {}  # user_id를 키로 하여 중복 제거
        for ws in self.active_connections[room_id]:
            if ws in self.user_info and self.connection_status.get(ws, False):
                user_info = self.user_info[ws]
                users[user_info["user_id"]] = {
                    "user_id": user_info["user_id"],
                    "user_name": user_info["user_name"],
                    "joined_at": user_info["joined_at"].isoformat()
                }
        return list(users.values())

    def get_room_count(self, room_id: str) -> int:
        """방의 활성 사용자 수"""
        return len(self.get_room_users(room_id))

    def is_room_empty(self, room_id: str) -> bool:
        """방이 비어있는지 확인"""
        return self.get_room_count(room_id) == 0

    async def ping_all_connections(self):
        """모든 연결에 ping 전송 (연결 상태 확인)"""
        ping_message = {
            "type": "ping",
            "data": {"timestamp": datetime.now().isoformat()}
        }
        
        for room_id in list(self.active_connections.keys()):
            await self.send_to_room(room_id, ping_message)

    def get_stats(self) -> dict:
        """연결 통계 정보"""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        active_rooms = len(self.active_connections)
        
        return {
            "total_connections": total_connections,
            "active_rooms": active_rooms,
            "rooms": {
                room_id: len(connections) 
                for room_id, connections in self.active_connections.items()
            }
        }


# 전역 매니저 인스턴스
manager = ConnectionManager()


# 주기적으로 연결 상태 확인하는 백그라운드 태스크
async def connection_health_check():
    """연결 상태 주기적 확인"""
    while True:
        try:
            await manager.ping_all_connections()
            await asyncio.sleep(30)  # 30초마다 ping
        except Exception as e:
            logger.error(f"Health check error: {e}")
            await asyncio.sleep(60)  # 오류 시 1분 대기
