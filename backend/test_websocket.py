import asyncio
import websockets
import json

async def test_user_connection(user_id, user_name, room_id="room_234243cd", family_id=1):
    uri = f"ws://127.0.0.1:8000/api/conversations/realtime/ws/{room_id}?user_id={user_id}&family_id={family_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"[{user_name}] 연결 성공: {uri}")
            
            # 입장 메시지 수신 대기
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"[{user_name}] 수신: {data}")
            except asyncio.TimeoutError:
                print(f"[{user_name}] 입장 메시지 수신 타임아웃")
            
            # 테스트 메시지 전송
            test_message = {
                "type": "message",
                "content": f"안녕하세요! {user_name}입니다."
            }
            await websocket.send(json.dumps(test_message))
            print(f"[{user_name}] 메시지 전송: {test_message['content']}")
            
            # 응답 대기
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"[{user_name}] 응답 수신: {data}")
            except asyncio.TimeoutError:
                print(f"[{user_name}] 응답 수신 타임아웃")
                
    except Exception as e:
        print(f"[{user_name}] 연결 실패: {e}")

async def main():
    print("=== WebSocket 연결 테스트 시작 ===")
    
    # 두 사용자 동시 연결 테스트
    await asyncio.gather(
        test_user_connection(9, "gaon"),
        test_user_connection(12, "gaon2")
    )

if __name__ == "__main__":
    asyncio.run(main())
