# backend/app/domains/practice/schemas.py

from __future__ import annotations

from enum import Enum
from datetime import datetime
from typing import List

from pydantic import BaseModel


class PracticeMode(str, Enum):
    """연습 모드 (채팅 / 음성)."""
    chat = "chat"
    voice = "voice"


class StartPracticeRequest(BaseModel):
    """연습 세션 생성 요청 바디.

    프론트에서 보내는 JSON:
    {
      "conversationId": "conv_xxx",
      "mode": "chat"
    }
    """
    conversationId: str
    mode: PracticeMode


class StartPracticeResponse(BaseModel):
    """연습 세션 생성 응답.

    프론트에서 기대하는 JSON:
    {
      "sessionId": "...",
      "conversationId": "...",
      "mode": "chat",
      "createdAt": "ISO8601..."
    }
    """
    sessionId: str
    conversationId: str
    mode: PracticeMode
    createdAt: datetime


class ChatRole(str, Enum):
  """연습 채팅에서의 화자 구분."""
  user = "user"
  assistant = "assistant"


class PracticeChatMessage(BaseModel):
  """연습 채팅 한 줄.

  프론트의 ChatMessage와 거의 1:1 매핑.
  """
  role: ChatRole
  content: str
  createdAt: datetime


class SubmitPracticeLogsRequest(BaseModel):
  """
  연습 종료 시 서버로 보내는 전체 채팅 로그.
  프론트에서 보내는 JSON 예시:
  {
    "messages": [
      { "role": "user", "content": "...", "createdAt": "2025-11-17T..." },
      { "role": "assistant", "content": "...", "createdAt": "..." }
    ]
  }
  """
  messages: List[PracticeChatMessage]


class PracticeCheckpoint(BaseModel):
    """분석 페이지의 체크 포인트 수행 여부."""
    id: str
    title: str
    achieved: bool
    description: str


class PracticeResult(BaseModel):
    """연습 결과 응답 스펙.

    프론트의 PracticeResult 타입과 1:1로 맞춤.
    """
    sessionId: str
    conversationId: str
    mode: PracticeMode
    score: float  # 0.0 ~ 1.0
    strengths: List[str]
    improvements: List[str]
    checkpoints: List[PracticeCheckpoint]
    summary: str
    createdAt: datetime