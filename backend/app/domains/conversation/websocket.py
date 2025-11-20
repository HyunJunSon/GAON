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
        # 사용자별 연결 관리 (초대 알림용)
        self.user_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, conversation_id: str):
        """클라이언트 연결"""
        await websocket.accept()
        
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        
        self.active_connections[conversation_id].append(websocket)
        logger.info(f"WebSocket 연결: conversation_id={conversation_id}")
    
    async def connect_user(self, websocket: WebSocket, user_email: str):
        """사용자별 WebSocket 연결"""
        await websocket.accept()
        
        if user_email not in self.user_connections:
            self.user_connections[user_email] = []
        
        self.user_connections[user_email].append(websocket)
        logger.info(f"사용자 WebSocket 연결: user_email={user_email}")
    
    def disconnect(self, websocket: WebSocket, conversation_id: str):
        """클라이언트 연결 해제"""
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)
            
            # 연결된 클라이언트가 없으면 키 삭제
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
        
        logger.info(f"WebSocket 연결 해제: conversation_id={conversation_id}")
    
    def disconnect_user(self, websocket: WebSocket, user_email: str):
        """사용자 WebSocket 연결 해제"""
        if user_email in self.user_connections:
            if websocket in self.user_connections[user_email]:
                self.user_connections[user_email].remove(websocket)
            
            if not self.user_connections[user_email]:
                del self.user_connections[user_email]
        
        logger.info(f"사용자 WebSocket 연결 해제: user_email={user_email}")
    
    async def send_to_user(self, user_email: str, message: dict):
        """특정 사용자에게 알림 전송"""
        logger.info(f"📨 사용자 알림 전송: user_email={user_email}")
        
        if user_email not in self.user_connections:
            logger.warning(f"📨 연결된 사용자 없음: user_email={user_email}")
            return
        
        disconnected = []
        success_count = 0
        
        for websocket in self.user_connections[user_email]:
            try:
                safe_message = self._make_json_safe(message)
                await websocket.send_text(json.dumps(safe_message))
                success_count += 1
                logger.debug(f"📨 사용자 알림 전송 성공")
            except Exception as e:
                logger.warning(f"📨 사용자 알림 전송 실패: {e}")
                disconnected.append(websocket)
        
        # 끊어진 연결 정리
        for ws in disconnected:
            self.disconnect_user(ws, user_email)
        
        logger.info(f"📨 사용자 알림 전송 완료: 성공={success_count}, 실패={len(disconnected)}")
    
    async def send_to_conversation(self, conversation_id: str, message: dict):
        """특정 대화의 모든 클라이언트에게 메시지 전송"""
        logger.info(f"📡 WebSocket 메시지 전송 시도: conversation_id={conversation_id}")
        
        if conversation_id not in self.active_connections:
            logger.warning(f"📡 연결된 클라이언트 없음: conversation_id={conversation_id}")
            return
        
        client_count = len(self.active_connections[conversation_id])
        logger.info(f"📡 연결된 클라이언트 수: {client_count}")
        
        # 연결이 끊어진 클라이언트 제거를 위한 리스트
        disconnected = []
        success_count = 0
        
        for websocket in self.active_connections[conversation_id]:
            try:
                # JSON 직렬화 안전성 확보
                safe_message = self._make_json_safe(message)
                await websocket.send_text(json.dumps(safe_message))
                success_count += 1
                logger.debug(f"📡 클라이언트 전송 성공")
            except Exception as e:
                logger.warning(f"📡 WebSocket 전송 실패: {e}")
                disconnected.append(websocket)
        
        # 끊어진 연결 정리
        for ws in disconnected:
            self.disconnect(ws, conversation_id)
        
        logger.info(f"📡 메시지 전송 완료: 성공={success_count}, 실패={len(disconnected)}")
    
    def _make_json_safe(self, obj):
        """JSON 직렬화 안전한 객체로 변환"""
        if isinstance(obj, dict):
            return {k: self._make_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_safe(item) for item in obj]
        elif hasattr(obj, '__str__') and not isinstance(obj, (str, int, float, bool, type(None))):
            return str(obj)  # UUID 등을 문자열로 변환
        else:
            return obj
    
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


async def user_websocket_endpoint(websocket: WebSocket, user_email: str):
    """사용자별 WebSocket 엔드포인트 (초대 알림용)"""
    await manager.connect_user(websocket, user_email)
    
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect_user(websocket, user_email)
    except Exception as e:
        logger.error(f"사용자 WebSocket 오류: {e}")
        manager.disconnect_user(websocket, user_email)


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
    logger.info(f"📡 분석 완료 알림 전송: conversation_id={conversation_id}, result={result}")
    try:
        await manager.broadcast_completion(conversation_id, result)
        logger.info(f"📡 분석 완료 알림 전송 성공")
    except Exception as e:
        logger.error(f"📡 분석 완료 알림 전송 실패: {e}")


async def notify_analysis_error(conversation_id: str, error: str):
    """분석 실패 알림"""
    logger.info(f"📡 분석 실패 알림 전송: conversation_id={conversation_id}, error={error}")
    try:
        await manager.broadcast_error(conversation_id, error)
        logger.info(f"📡 분석 실패 알림 전송 성공")
    except Exception as e:
        logger.error(f"📡 분석 실패 알림 전송 실패: {e}")


async def send_family_invite_notification(user_email: str, inviter_name: str, family_name: str, member_id: int):
    """가족 초대 알림 전송"""
    logger.info(f"📨 가족 초대 알림 전송: user_email={user_email}, inviter={inviter_name}")
    
    message = {
        "type": "family_invite",
        "data": {
            "title": "가족 초대",
            "message": f"{inviter_name}님이 '{family_name}'에 초대했습니다.",
            "inviterName": inviter_name,
            "familyName": family_name,
            "memberId": member_id,
            "actions": [
                {"type": "accept", "label": "수락"},
                {"type": "decline", "label": "거절"}
            ]
        }
    }
    
    try:
        await manager.send_to_user(user_email, message)
        logger.info(f"📨 가족 초대 알림 전송 성공")
    except Exception as e:
        logger.error(f"📨 가족 초대 알림 전송 실패: {e}")
