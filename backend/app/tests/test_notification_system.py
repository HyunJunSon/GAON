"""
알림 시스템 테스트
- WebSocket 연결 관리 테스트
- 실시간 진행률 업데이트 테스트
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.domains.conversation.websocket import (
    ConnectionManager,
    update_analysis_progress,
    notify_analysis_complete,
    notify_analysis_error
)


class TestConnectionManager:
    """WebSocket 연결 관리자 테스트"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.manager = ConnectionManager()
        self.mock_websocket = MagicMock()
        self.mock_websocket.send_text = AsyncMock()
        self.conversation_id = "test-conv-id"
    
    @pytest.mark.asyncio
    async def test_connect_websocket(self):
        """WebSocket 연결 테스트"""
        self.mock_websocket.accept = AsyncMock()
        
        await self.manager.connect(self.mock_websocket, self.conversation_id)
        
        assert self.conversation_id in self.manager.active_connections
        assert self.mock_websocket in self.manager.active_connections[self.conversation_id]
        self.mock_websocket.accept.assert_called_once()
        
        print("✅ WebSocket 연결 테스트 통과")
    
    def test_disconnect_websocket(self):
        """WebSocket 연결 해제 테스트"""
        # 먼저 연결 추가
        self.manager.active_connections[self.conversation_id] = [self.mock_websocket]
        
        # 연결 해제
        self.manager.disconnect(self.mock_websocket, self.conversation_id)
        
        assert self.conversation_id not in self.manager.active_connections
        print("✅ WebSocket 연결 해제 테스트 통과")
    
    @pytest.mark.asyncio
    async def test_send_to_conversation(self):
        """대화별 메시지 전송 테스트"""
        # 연결 설정
        self.manager.active_connections[self.conversation_id] = [self.mock_websocket]
        
        test_message = {"type": "test", "data": "test_data"}
        
        await self.manager.send_to_conversation(self.conversation_id, test_message)
        
        self.mock_websocket.send_text.assert_called_once()
        print("✅ 메시지 전송 테스트 통과")
    
    @pytest.mark.asyncio
    async def test_broadcast_progress(self):
        """진행률 브로드캐스트 테스트"""
        # 연결 설정
        self.manager.active_connections[self.conversation_id] = [self.mock_websocket]
        
        progress_data = {
            "currentStep": "cleaner",
            "progress": 30,
            "stepProgress": {
                "cleaner": {"status": "running", "progress": 30}
            }
        }
        
        await self.manager.broadcast_progress(self.conversation_id, progress_data)
        
        # 메시지 형식 확인
        call_args = self.mock_websocket.send_text.call_args[0][0]
        import json
        sent_message = json.loads(call_args)
        
        assert sent_message["type"] == "analysis_progress"
        assert sent_message["conversationId"] == self.conversation_id
        assert sent_message["data"] == progress_data
        
        print("✅ 진행률 브로드캐스트 테스트 통과")
    
    @pytest.mark.asyncio
    async def test_broadcast_completion(self):
        """완료 알림 브로드캐스트 테스트"""
        # 연결 설정
        self.manager.active_connections[self.conversation_id] = [self.mock_websocket]
        
        result_data = {
            "status": "completed",
            "score": 85,
            "confidence": 0.9
        }
        
        await self.manager.broadcast_completion(self.conversation_id, result_data)
        
        # 메시지 형식 확인
        call_args = self.mock_websocket.send_text.call_args[0][0]
        import json
        sent_message = json.loads(call_args)
        
        assert sent_message["type"] == "analysis_complete"
        assert sent_message["data"] == result_data
        
        print("✅ 완료 알림 브로드캐스트 테스트 통과")
    
    @pytest.mark.asyncio
    async def test_broadcast_error(self):
        """에러 알림 브로드캐스트 테스트"""
        # 연결 설정
        self.manager.active_connections[self.conversation_id] = [self.mock_websocket]
        
        error_message = "분석 중 오류 발생"
        
        await self.manager.broadcast_error(self.conversation_id, error_message)
        
        # 메시지 형식 확인
        call_args = self.mock_websocket.send_text.call_args[0][0]
        import json
        sent_message = json.loads(call_args)
        
        assert sent_message["type"] == "analysis_failed"
        assert sent_message["data"]["error"] == error_message
        
        print("✅ 에러 알림 브로드캐스트 테스트 통과")


class TestNotificationFunctions:
    """알림 함수 테스트"""
    
    @pytest.mark.asyncio
    async def test_update_analysis_progress(self):
        """분석 진행률 업데이트 함수 테스트"""
        # 함수 존재 및 호출 가능 확인
        try:
            await update_analysis_progress(
                conversation_id="test-id",
                current_step="cleaner",
                progress=50,
                step_progress={
                    "cleaner": {"status": "running", "progress": 50}
                }
            )
            print("✅ 분석 진행률 업데이트 함수 테스트 통과")
        except Exception as e:
            pytest.fail(f"분석 진행률 업데이트 함수 실행 실패: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_notify_analysis_complete(self):
        """분석 완료 알림 함수 테스트"""
        try:
            await notify_analysis_complete(
                conversation_id="test-id",
                result={"status": "completed", "score": 90}
            )
            print("✅ 분석 완료 알림 함수 테스트 통과")
        except Exception as e:
            pytest.fail(f"분석 완료 알림 함수 실행 실패: {str(e)}")
    
    @pytest.mark.asyncio
    async def test_notify_analysis_error(self):
        """분석 실패 알림 함수 테스트"""
        try:
            await notify_analysis_error(
                conversation_id="test-id",
                error="테스트 에러"
            )
            print("✅ 분석 실패 알림 함수 테스트 통과")
        except Exception as e:
            pytest.fail(f"분석 실패 알림 함수 실행 실패: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
