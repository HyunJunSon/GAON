"""간단한 Cleaner 그래프 구현 (LangGraph 기반으로 확장 가능)

이 파일은 프로젝트의 Cleaner 파이프라인 진입점 역할을 하는
`CleanerGraph` 클래스를 제공합니다. 실제 LangGraph 연동은
나중에 추가할 수 있도록 run() 스텁만 둡니다.
"""

from __future__ import annotations
from typing import Any


class CleanerGraph:
    """Cleaner 단계의 그래프를 나타내는 가벼운 래퍼 클래스.

    제공되는 메서드는 다음과 같습니다:
    - run(raw): 원시 입력을 받아 전처리/정제 파이프라인을 실행
    """

    def __init__(self) -> None:
        # 필요한 구성값이나 노드 레퍼런스는 여기에서 주입할 수 있음
        pass

    def run(self, raw: Any) -> dict:
        """원시 데이터를 받아 정제된 대화(또는 에러)를 반환하는 간단한 스텁.

        실제 구현에서는 LangGraph 노드들을 연결하고 실행한 뒤
        결과를 조합해서 반환합니다. 여기서는 최소한의 형태로
        dict을 반환합니다.
        """
        # TODO: LangGraph 노드 연결 및 실행
        return {"status": "ok", "data": raw}


__all__ = ["CleanerGraph"]
