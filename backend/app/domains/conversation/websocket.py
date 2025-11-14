"""
WebSocket을 통한 실시간 분석 진행률 알림
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        # conversation_id별로 연결된 클라이언트들 관리
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, conversation_id: str):
        """클라이언트 연결"""
        await websocket.accept()
        
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        
        self.active_connections[conversation_id].append(websocket)
        logger.info(f"WebSocket 연결: conversation_id={conversation_id}")
    
    def disconnect(self, websocket: WebSocket, conversation_id: str):
        """클라이언트 연결 해제"""
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)
            
            # 연결된 클라이언트가 없으면 키 삭제
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
        
        logger.info(f"WebSocket 연결 해제: conversation_id={conversation_id}")
    
    async def send_to_conversation(self, conversation_id: str, message: dict):
        """특정 대화의 모든 클라이언트에게 메시지 전송"""
        if conversation_id not in self.active_connections:
            return
        
        # 연결이 끊어진 클라이언트 제거를 위한 리스트
        disconnected = []
        
        for websocket in self.active_connections[conversation_id]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"WebSocket 전송 실패: {e}")
                disconnected.append(websocket)
        
        # 끊어진 연결 정리
        for ws in disconnected:
            self.disconnect(ws, conversation_id)
    
    async def broadcast_progress(self, conversation_id: str, progress_data: dict):
        """분석 진행률 브로드캐스트"""
        message = {
            "type": "analysis_progress",
            "conversationId": conversation_id,
            "data": progress_data
        }
        await self.send_to_conversation(conversation_id, message)
    
    async def broadcast_completion(self, conversation_id: str, result_data: dict):
        """분석 완료 브로드캐스트"""
        message = {
            "type": "analysis_complete",
            "conversationId": conversation_id,
            "data": result_data
        }
        await self.send_to_conversation(conversation_id, message)
    
    async def broadcast_error(self, conversation_id: str, error_message: str):
        """분석 실패 브로드캐스트"""
        message = {
            "type": "analysis_failed",
            "conversationId": conversation_id,
            "data": {"error": error_message}
        }
        await self.send_to_conversation(conversation_id, message)


# 전역 연결 관리자 인스턴스
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """WebSocket 엔드포인트"""
    await manager.connect(websocket, conversation_id)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신 (keep-alive)
            data = await websocket.receive_text()
            
            # 필요시 클라이언트 메시지 처리
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)
    except Exception as e:
        logger.error(f"WebSocket 오류: {e}")
        manager.disconnect(websocket, conversation_id)


# Agent 파이프라인에서 사용할 진행률 업데이트 함수들
async def update_analysis_progress(
    conversation_id: str,
    current_step: str,
    progress: int,
    step_progress: dict,
    estimated_time_remaining: int = None
):
    """분석 진행률 업데이트"""
    progress_data = {
        "conversationId": conversation_id,
        "currentStep": current_step,
        "progress": progress,
        "stepProgress": step_progress,
        "estimatedTimeRemaining": estimated_time_remaining
    }
    
    await manager.broadcast_progress(conversation_id, progress_data)


async def notify_analysis_complete(conversation_id: str, result: dict):
    """분석 완료 알림"""
    await manager.broadcast_completion(conversation_id, result)


async def notify_analysis_error(conversation_id: str, error: str):
    """분석 실패 알림"""
    await manager.broadcast_error(conversation_id, error)
