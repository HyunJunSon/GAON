"""간단한 Analysis 그래프 스텁

실제 LLM 기반 분석 로직은 이 클래스의 run() 내부에 연결하면 됩니다.
"""

from typing import Any


class AnalysisGraph:
    def __init__(self) -> None:
        pass

    def run(self, conversation: Any) -> dict:
        """대화를 받아 분석 결과(감정·스타일·통계 등)를 반환하는 스텁."""
        # TODO: LLM/분석 로직 연결
        return {"status": "ok", "analysis": {}}


__all__ = ["AnalysisGraph"]
