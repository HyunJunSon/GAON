"""간단한 노드 플레이스홀더

실제 구현 시 각 노드는 LangGraph 노드 혹은 함수로 대체됩니다.
여기서는 이름만 정의한 가벼운 플레이스홀더를 제공합니다.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class RawFetcher:
    def fetch(self) -> Any:
        return None


@dataclass
class RawInspector:
    def inspect(self, raw: Any) -> bool:
        return True


@dataclass
class ConversationCleaner:
    def clean(self, raw: Any) -> Any:
        return raw


@dataclass
class ExceptionHandler:
    def handle(self, raw: Any) -> None:
        pass


@dataclass
class ConversationValidator:
    def validate(self, convo: Any) -> bool:
        return True


@dataclass
class ConversationSaver:
    def save(self, convo: Any) -> int:
        return 1


__all__ = [
    "RawFetcher",
    "RawInspector",
    "ConversationCleaner",
    "ExceptionHandler",
    "ConversationValidator",
    "ConversationSaver",
]
