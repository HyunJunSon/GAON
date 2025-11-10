from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .websocket_manager import manager
import json
import base64

router = APIRouter()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "audio":
                # 음성 데이터를 텍스트로 변환 (STT)
                audio_data = base64.b64decode(message["audio"])
                transcript = await convert_speech_to_text(audio_data)
                
                # 변환된 텍스트를 모든 참가자에게 전송
                await manager.send_to_session({
                    "type": "transcript",
                    "content": transcript,
                    "user_id": message.get("user_id"),
                    "is_final": message.get("is_final", False)
                }, session_id)
            
            elif message["type"] == "text":
                # 일반 텍스트 메시지
                await manager.send_to_session({
                    "type": "message",
                    "content": message["content"],
                    "user_id": message.get("user_id")
                }, session_id)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

async def convert_speech_to_text(audio_data: bytes) -> str:
    # 간단한 STT 구현 (OpenAI Whisper 사용)
    try:
        from openai import OpenAI
        client = OpenAI()
        
        # 임시 파일로 저장
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav") as temp_file:
            temp_file.write(audio_data)
            temp_file.flush()
            
            # Whisper로 변환
            with open(temp_file.name, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                return transcript.text
    except:
        return "[음성 변환 실패]"
