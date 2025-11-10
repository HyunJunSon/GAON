import asyncio
import websockets
import json

async def test_bidirectional_chat():
    room_id = "room_234243cd"
    family_id = 1
    
    # 사용자 A 연결
    uri_a = f"ws://127.0.0.1:8000/api/conversations/realtime/ws/{room_id}?user_id=9&family_id={family_id}"
    # 사용자 B 연결  
    uri_b = f"ws://127.0.0.1:8000/api/conversations/realtime/ws/{room_id}?user_id=12&family_id={family_id}"
    
    async def user_a_handler():
        async with websockets.connect(uri_a) as ws_a:
            print("[gaon] 연결됨")
            
            # 입장 메시지들 수신
            for i in range(2):  # 자신과 상대방 입장 메시지
                try:
                    msg = await asyncio.wait_for(ws_a.recv(), timeout=3.0)
                    data = json.loads(msg)
                    print(f"[gaon] 입장 메시지: {data.get('data', {}).get('message', 'N/A')}")
                except asyncio.TimeoutError:
                    break
            
            # 메시지 전송
            await asyncio.sleep(1)  # 잠시 대기
            test_msg = {"type": "message", "content": "gaon에서 보내는 메시지"}
            await ws_a.send(json.dumps(test_msg))
            print("[gaon] 메시지 전송:", test_msg["content"])
            
            # 응답 및 상대방 메시지 수신 대기
            for i in range(3):
                try:
                    response = await asyncio.wait_for(ws_a.recv(), timeout=5.0)
                    data = json.loads(response)
                    if data.get("type") == "message":
                        sender = data.get("data", {}).get("user_name", "Unknown")
                        content = data.get("data", {}).get("message", "")
                        print(f"[gaon] 메시지 수신 from {sender}: {content}")
                except asyncio.TimeoutError:
                    print("[gaon] 메시지 수신 타임아웃")
                    break
    
    async def user_b_handler():
        await asyncio.sleep(0.5)  # A가 먼저 연결되도록 대기
        async with websockets.connect(uri_b) as ws_b:
            print("[gaon2] 연결됨")
            
            # 입장 메시지 수신
            try:
                msg = await asyncio.wait_for(ws_b.recv(), timeout=3.0)
                data = json.loads(msg)
                print(f"[gaon2] 입장 메시지: {data.get('data', {}).get('message', 'N/A')}")
            except asyncio.TimeoutError:
                pass
            
            # 상대방 메시지 대기 후 응답
            await asyncio.sleep(2)  # A의 메시지 대기
            
            # 메시지 전송
            test_msg = {"type": "message", "content": "gaon2에서 보내는 답장"}
            await ws_b.send(json.dumps(test_msg))
            print("[gaon2] 메시지 전송:", test_msg["content"])
            
            # 메시지 수신 대기
            for i in range(3):
                try:
                    response = await asyncio.wait_for(ws_b.recv(), timeout=5.0)
                    data = json.loads(response)
                    if data.get("type") == "message":
                        sender = data.get("data", {}).get("user_name", "Unknown")
                        content = data.get("data", {}).get("message", "")
                        print(f"[gaon2] 메시지 수신 from {sender}: {content}")
                except asyncio.TimeoutError:
                    print("[gaon2] 메시지 수신 타임아웃")
                    break
    
    # 두 사용자 동시 실행
    await asyncio.gather(user_a_handler(), user_b_handler())

if __name__ == "__main__":
    print("=== 양방향 채팅 테스트 ===")
    asyncio.run(test_bidirectional_chat())
