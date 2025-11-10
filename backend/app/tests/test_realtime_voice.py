import pytest
from fastapi.testclient import TestClient
from app.main import app
import json
import base64

client = TestClient(app)

def test_websocket_connection():
    """WebSocket 연결 테스트"""
    with client.websocket_connect("/realtime/ws/test-session") as websocket:
        # 텍스트 메시지 전송
        websocket.send_text(json.dumps({
            "type": "text",
            "content": "안녕하세요",
            "user_id": "test-user"
        }))
        
        # 응답 받기
        data = websocket.receive_text()
        message = json.loads(data)
        
        assert message["type"] == "message"
        assert message["content"] == "안녕하세요"

def test_audio_to_text():
    """음성 → 텍스트 변환 테스트"""
    # 더미 오디오 데이터
    dummy_audio = b"dummy audio data"
    audio_b64 = base64.b64encode(dummy_audio).decode()
    
    with client.websocket_connect("/realtime/ws/test-session") as websocket:
        websocket.send_text(json.dumps({
            "type": "audio",
            "audio": audio_b64,
            "user_id": "test-user",
            "is_final": True
        }))
        
        # STT 결과 받기
        data = websocket.receive_text()
        message = json.loads(data)
        
        assert message["type"] == "transcript"
        assert "content" in message
