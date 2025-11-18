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

# 세션별 분석 결과 캐시: 세션ID -> 결과
_PRACTICE_RESULTS: Dict[str, PracticeResult] = {}

# 세션별 채팅 로그 저장소 (임시, 인메모리): sessionId → [PracticeMessage, ...]
_PRACTICE_LOGS: Dict[str, List[PracticeChatMessage]] = {}

def _analyze_practice_session(
    session: StartPracticeResponse,
    log: SubmitPracticeLogsRequest | None,
) -> PracticeResult:
    """연습 세션 + 로그를 기반으로 결과를 생성하는 임시 분석 함수.

    지금은 로그 내용을 실제로 쓰진 않고,
    세션 정보가 있다는 정도만 활용해서 목업 결과를 만든다.
    나중에는 log.messages 내용을 바탕으로 LLM 분석 결과를 생성하도록 교체.
    """
    now = datetime.utcnow()
    msgs = log or []

    user_msgs = [m for m in msgs if m.role == "user"]
    assistant_msgs = [m for m in msgs if m.role == "assistant"]

    # 아주 단순한 예시 통계
    user_len = sum(len(m.content) for m in user_msgs)
    other_len = sum(len(m.content) for m in assistant_msgs)

    base_score = 0.8
    score = base_score
    if user_len > other_len:
        score = min(1.0, base_score + 0.05)

    # TODO: log.messages를 바탕으로 통계/피드백 생성
    return PracticeResult(
        sessionId=session.sessionId,
        conversationId=session.conversationId,
        mode=session.mode,
        score=score,
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
                description="“그때 많이 힘들었겠다”처럼 감정을 먼저 언급한 부분이 있었어요.",
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
            "다음 연습에서는 1) 감정 요약 → 2) 상황 정리 → 3) 자신의 바람/요청 순서로 말하는 패턴을 "
            "의식적으로 연습해보는 것을 추천드립니다."
        ),
        createdAt=now,
    )


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

    - 먼저 캐시된 결과가 있으면 반환
    - 없으면 로그를 찾아서 분석을 한 번 수행
    - 세션이나 로그가 없으면 예외
    """
    session = _PRACTICE_SESSIONS.get(session_id)
    if session is None:
        raise KeyError(f"practice session not found: {session_id}")

    # 이미 결과가 있다면 그대로 반환
    if session_id in _PRACTICE_RESULTS:
        return _PRACTICE_RESULTS[session_id]

    log = _PRACTICE_LOGS.get(session_id)
    if log is None:
        # 아직 연습 종료를 안 해서 로그가 없다고 판단
        raise KeyError(f"practice log not found for session: {session_id}")

    result = _analyze_practice_session(session, log)
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
    # 로그가 바뀌었으니, 이전 분석 결과는 더 이상 유효하지 않을 수 있음 → 캐시 삭제
    if session_id in _PRACTICE_RESULTS:
        del _PRACTICE_RESULTS[session_id]

    # TODO:
    #  - 여기서 payload.messages를 기반으로
    #    LLM/에이전트 호출 → PracticeResult 생성/업데이트 로직을 붙이면 됨


def finish_practice_session(
    session_id: str,
    payload: SubmitPracticeLogsRequest,
) -> PracticeResult:
    """연습 종료 처리.

    - 세션 유효성 검증
    - 로그 저장
    - 분석 로직 호출
    - 결과 캐싱 후 반환
    """
    session = _PRACTICE_SESSIONS.get(session_id)
    if session is None:
        raise KeyError(f"practice session not found: {session_id}")

    # 로그 저장
    _PRACTICE_LOGS[session_id] = payload

    # 분석 실행 (현재는 목업)
    result = _analyze_practice_session(session, payload)

    # 결과 캐시
    _PRACTICE_RESULTS[session_id] = result
    return result