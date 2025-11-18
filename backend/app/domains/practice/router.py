# backend/app/domains/practice/router.py

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect
from typing import AsyncIterator
import asyncio

from .schemas import (
    StartPracticeRequest,
    StartPracticeResponse,
    PracticeResult,
    SubmitPracticeLogsRequest,
)
from .services import (
    start_practice_session,
    get_practice_result,
    submit_practice_logs,
)

router = APIRouter(
    prefix="/api/practice",
    tags=["practice"],
)


@router.post(
    "/session",
    response_model=StartPracticeResponse,
    summary="연습 세션 시작",
)
def create_practice_session(body: StartPracticeRequest) -> StartPracticeResponse:
    """연습 세션을 생성하고 세션 ID를 반환한다.

    프론트 플로우:
    - /practice 페이지에서 '실시간 채팅 / 음성 연습 시작' 클릭
    - conversationId + mode를 보내서 sessionId를 발급받음
    - 응답으로 받은 sessionId로 /practice/chat/{sessionId}?mode=... 로 이동
    """
    return start_practice_session(body)


@router.get(
    "/result/{session_id}",
    response_model=PracticeResult,
    summary="연습 결과 조회",
)
def read_practice_result(session_id: str) -> PracticeResult:
    """연습 결과를 조회한다.

    프론트 플로우:
    - /practice/chat/{sessionId}에서 '연습 종료하기'를 누르면
    - /practice/result/{sessionId}로 이동
    - 이 엔드포인트에서 결과를 가져와서 화면에 보여줌
    """
    try:
        return get_practice_result(session_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="연습 세션을 찾을 수 없습니다.",
        )
    

@router.post(
    "/session/{session_id}/logs",
    status_code=status.HTTP_200_OK,
    summary="연습 세션 로그 제출",
)
def submit_logs(
    session_id: str,
    body: SubmitPracticeLogsRequest,
) -> None:
    """연습 종료 시 채팅 로그를 서버로 전송.

    프론트 플로우:
    - /practice/chat/{sessionId}에서 '연습 종료하기' 클릭
    - 현재까지의 messages 배열을 이 엔드포인트로 전송
    - 204 응답을 받으면 /practice/result/{sessionId} 로 이동
    """
    try:
        submit_practice_logs(session_id, body)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="연습 세션을 찾을 수 없습니다.",
        )
    
# --- 텍스트 LLM 스트리밍 목업 (나중에 LangGraph/LLM으로 교체 예정) ---

async def _fake_llm_stream(user_text: str) -> AsyncIterator[str]:
    """사용자 입력을 받아서 토막 토막 흉내내며 응답을 스트리밍하는 목업.

    나중에는 여기에서 LangGraph/LLM 스트리밍 호출로 교체하면 된다.
    """
    base = (
        "그렇게 느낄 수 있어요. "
        "조금만 더 구체적으로 어떤 상황이었는지 설명해주실 수 있을까요? "
        "그러면 가족과 어떻게 말하면 좋을지 같이 정리해볼게요."
    )

    # 아주 단순하게 10~15 글자씩 끊어서 흉내
    chunk_size = 15
    for i in range(0, len(base), chunk_size):
        await asyncio.sleep(0.12)  # 토큰 나오는 느낌만 연출
        yield base[i : i + chunk_size]

# --- WebSocket: 실시간 텍스트 연습용 ---


@router.websocket("/ws/{session_id}")
async def practice_ws(websocket: WebSocket, session_id: str) -> None:
    """연습 세션용 텍스트 WebSocket.

    프로토콜 (JSON 텍스트):
    - 클라이언트 → 서버:
      { "type": "user_text", "content": "<사용자 입력>" }

    - 서버 → 클라이언트:
      1) 스트리밍 응답:
         { "type": "assistant_delta", "content": "<부분 텍스트>" } ...
         { "type": "assistant_done" }

      2) 에러:
         { "type": "error", "message": "<오류 설명>" }
    """
    # 핸드셰이크
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            # 간단하게 JSON 파싱
            try:
                import json

                payload = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(
                    '{"type":"error","message":"invalid json"}'
                )
                continue

            msg_type = payload.get("type")
            content = payload.get("content")

            if msg_type != "user_text" or not isinstance(content, str):
                await websocket.send_text(
                    '{"type":"error","message":"unsupported message type"}'
                )
                continue

            # TODO: 여기서 session_id 검증, 유저 인증, 세션 로깅 등 추가 가능

            # 1) 먼저 사용자의 발화를 서버 로그에 넣고 싶다면,
            #    services.submit_practice_logs 등에 통합 가능 (지금은 생략)

            # 2) LLM 스트리밍 응답 보내기 (목업 버전)
            async for chunk in _fake_llm_stream(content):
                out = {"type": "assistant_delta", "content": chunk}
                await websocket.send_text(json.dumps(out))

            # 3) 스트리밍 종료 표시
            await websocket.send_text('{"type":"assistant_done"}')

    except WebSocketDisconnect:
        # 클라이언트가 연결 끊었을 때 조용히 종료
        return
    except Exception as exc:
        # 예상 못한 에러는 클라이언트에 한 번 알려주고 종료
        import json
        await websocket.send_text(
            json.dumps(
                {"type": "error", "message": f"internal error: {exc}"}
            )
        )
        await websocket.close()