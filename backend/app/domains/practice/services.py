# backend/app/domains/practice/services.py

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from uuid import uuid4

from .schemas import (
    PracticeMode,
    PracticeResult,
    PracticeCheckpoint,
    StartPracticeRequest,
    StartPracticeResponse,
    PracticeChatMessage,
    SubmitPracticeLogsRequest
)

# TODO:
#  - 현재는 메모리 상에만 세션/결과를 저장하는 임시 구현
#  - 추후에는 DB 테이블 (practice_sessions, practice_results 등)로 대체 필요

# 세션ID -> 대화ID / 모드 매핑
_PRACTICE_SESSIONS: Dict[str, StartPracticeResponse] = {}

# 세션ID -> 결과
_PRACTICE_RESULTS: Dict[str, PracticeResult] = {}

# 🔹 새로 추가: 세션별 채팅 로그 저장소 (임시, 인메모리)
_PRACTICE_LOGS: Dict[str, List[PracticeChatMessage]] = {}

def start_practice_session(
    payload: StartPracticeRequest,
) -> StartPracticeResponse:
    """연습 세션 생성.

    - 세션 ID를 발급하고
    - (임시) 메모리에 저장한 뒤
    - 프론트에 세션 정보를 반환한다.
    """
    session_id = f"s_{uuid4().hex[:10]}"
    now = datetime.utcnow()

    session = StartPracticeResponse(
        sessionId=session_id,
        conversationId=payload.conversationId,
        mode=payload.mode,
        createdAt=now,
    )
    _PRACTICE_SESSIONS[session_id] = session

    # 실제 구현에서는 여기서:
    #  - 대화 내용을 가져와서
    #  - LLM 에이전트에 초기 컨텍스트로 전달하는 작업 등이 들어갈 수 있음

    return session


def get_practice_result(session_id: str) -> PracticeResult:
    """연습 결과 조회.

    1차 버전:
      - 세션 정보가 있으면 그걸 기반으로 목업 결과를 생성
      - 실제로는 session_id를 기준으로 DB에서 결과를 읽어오게 됨
    """
    session = _PRACTICE_SESSIONS.get(session_id)
    if session is None:
        # 실제 서비스에서는 커스텀 예외를 던지고 FastAPI에서 404로 변환
        raise KeyError(f"practice session not found: {session_id}")

    # 이미 결과가 만들어져 있다면 재사용 (임시 캐시)
    if session_id in _PRACTICE_RESULTS:
        return _PRACTICE_RESULTS[session_id]

    now = datetime.utcnow()

    # TODO: 실제 LLM 분석 결과로 대체 예정
    result = PracticeResult(
        sessionId=session.sessionId,
        conversationId=session.conversationId,
        mode=session.mode,
        score=0.86,
        strengths=[
            "상대방의 감정을 인정하는 표현을 자주 사용했어요.",
            "질문을 통해 상대방의 생각을 이끌어내려는 시도가 좋았어요.",
        ],
        improvements=[
            "대화의 초반에 상황을 조금 더 구체적으로 설명해주면 좋아요.",
            "상대방의 말을 마무리까지 듣고 나서 자신의 의견을 말하는 연습이 필요해요.",
        ],
        checkpoints=[
            PracticeCheckpoint(
                id="cp1",
                title="상대방의 감정 먼저 되짚어주기",
                achieved=True,
                description=(
                    "“그때 많이 힘들었겠다”처럼 감정을 먼저 언급한 부분이 있었어요."
                ),
            ),
            PracticeCheckpoint(
                id="cp2",
                title="비난 대신 구체적인 요청 사용하기",
                achieved=False,
                description=(
                    "“그러니까 너는 항상…” 보다는 "
                    "“다음엔 이렇게 해줄 수 있을까?” 같은 표현을 더 연습해보면 좋아요."
                ),
            ),
        ],
        summary=(
            "이번 연습에서 사용자는 상대방의 감정을 인정하고 공감하려는 태도가 잘 드러났습니다.\n"
            "다만, 대화를 시작할 때 상황 설명이 다소 부족한 부분이 있었고,\n"
            "상대방의 말을 끝까지 듣기 전에 자신의 의견을 먼저 제시하는 장면이 몇 번 관찰되었습니다.\n\n"
            "다음 연습에서는,\n"
            "1) 감정 요약 → 2) 상황 정리 → 3) 자신의 바람/요청 순서로 말하는 패턴을 "
            "의식적으로 연습해보는 것을 추천드립니다."
        ),
        createdAt=now,
    )

    _PRACTICE_RESULTS[session_id] = result
    return result


def submit_practice_logs(
    session_id: str,
    payload: SubmitPracticeLogsRequest,
) -> None:
    """연습 종료 시 전달된 채팅 로그를 저장.

    - 1차 버전: 인메모리 dict에만 저장
    - 추후:
      - DB 테이블에 insert
      - 여기서 LLM 분석 작업 큐에 넣거나,
      - 바로 분석해서 PracticeResult 생성하도록 확장 가능
    """
    if session_id not in _PRACTICE_SESSIONS:
        raise KeyError(f"practice session not found: {session_id}")

    _PRACTICE_LOGS[session_id] = payload.messages

    # TODO:
    #  - 여기서 payload.messages를 기반으로
    #    LLM/에이전트 호출 → PracticeResult 생성/업데이트 로직을 붙이면 됨