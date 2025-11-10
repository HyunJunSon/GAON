import asyncio
import websockets
import json

async def test_free_chat():
    """자유 채팅 테스트"""
    room_id = "test_room_123"
    
    # 사용자 A
    uri_a = f"ws://127.0.0.1:8000/api/conversations/realtime/ws/{room_id}?user_id=1&user_name=Alice"
    # 사용자 B  
    uri_b = f"ws://127.0.0.1:8000/api/conversations/realtime/ws/{room_id}?user_id=2&user_name=Bob"
    
    async def user_handler(uri, user_name, messages_to_send):
        try:
            async with websockets.connect(uri) as websocket:
                print(f"[{user_name}] 연결됨")
                
                # 입장 메시지 수신
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    data = json.loads(msg)
                    print(f"[{user_name}] 입장: {data.get('data', {}).get('message', '')}")
                except asyncio.TimeoutError:
                    print(f"[{user_name}] 입장 메시지 타임아웃")
                
                # 메시지 전송
                for message in messages_to_send:
                    await asyncio.sleep(1)
                    test_msg = {"type": "message", "content": message}
                    await websocket.send(json.dumps(test_msg))
                    print(f"[{user_name}] 전송: {message}")
                
                # 메시지 수신 대기
                for _ in range(5):
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        data = json.loads(response)
                        if data.get("type") == "message":
                            sender = data.get("data", {}).get("user_name", "Unknown")
                            content = data.get("data", {}).get("message", "")
                            print(f"[{user_name}] 수신 from {sender}: {content}")
                    except asyncio.TimeoutError:
                        break
                        
        except Exception as e:
            print(f"[{user_name}] 오류: {e}")
    
    # 두 사용자 동시 테스트
    await asyncio.gather(
        user_handler(uri_a, "Alice", ["안녕하세요!", "잘 지내세요?"]),
        user_handler(uri_b, "Bob", ["안녕!", "네, 잘 지내고 있어요!"])
    )

if __name__ == "__main__":
    print("=== 자유 채팅 테스트 ===")
    asyncio.run(test_free_chat())
