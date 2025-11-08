from typing import Dict, List
from fastapi import WebSocket
import json
from datetime import datetime


class ConnectionManager:
    def __init__(self):
        # room_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # websocket -> user_info
        self.user_info: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: int, family_id: int, user_name: str = None):
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

    def disconnect(self, websocket: WebSocket):
        user_info = self.user_info.get(websocket)
        if user_info:
            room_id = user_info["room_id"]
            if room_id in self.active_connections:
                if websocket in self.active_connections[room_id]:
                    self.active_connections[room_id].remove(websocket)
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]
            del self.user_info[websocket]

    async def send_to_room(self, room_id: str, message: dict):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    # 연결이 끊어진 경우 제거
                    self.disconnect(connection)

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_text(json.dumps(message))
        except:
            self.disconnect(websocket)

    def get_room_users(self, room_id: str) -> List[int]:
        if room_id not in self.active_connections:
            return []
        
        users = []
        for ws in self.active_connections[room_id]:
            if ws in self.user_info:
                users.append(self.user_info[ws]["user_id"])
        return users


manager = ConnectionManager()
