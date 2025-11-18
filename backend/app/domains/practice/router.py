# backend/app/domains/practice/router.py

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

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