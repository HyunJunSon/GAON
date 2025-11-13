from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
import pandas as pd
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from .nodes import (
    Analyzer,
    ScoreEvaluator,
    AnalysisSaver,
)

# =====================================
# ✅ State 정의 (DB 세션 포함)
# =====================================
@dataclass
class AnalysisState:
    db: Optional[Session] = None

    conversation_df: Optional[pd.DataFrame] = None
    id: Optional[int] = None
    conv_id: Optional[str] = None
    analysis_result: Optional[Dict[str, Any]] = None

    validated: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)
    verbose: bool = True


# =====================================
# ✅ AnalysisGraph
# =====================================
class AnalysisGraph:
    def __init__(self, verbose=True):
        self.verbose = verbose

        # 🔧 Analyzer: 형태소 기반 MATTR + 통계 기반 스타일 분석 수행
        self.analyzer = Analyzer(verbose)

        self.evaluator = ScoreEvaluator()
        self.saver = AnalysisSaver(verbose)

        # =====================================
        # 🔧 Graph 빌드
        # → analyze → save 순서만 존재하는 2-step 파이프라인
        # =====================================
        self.graph = StateGraph(AnalysisState)

        self.graph.add_node("analyze", self.node_analyze)
        self.graph.add_node("save", self.node_save)

        self.graph.set_entry_point("analyze")
        self.graph.add_edge("analyze", "save")
        self.graph.add_edge("save", END)

        self.pipeline = self.graph.compile()

    # =====================================
    # Node Functions
    # =====================================

    def node_analyze(self, state: AnalysisState):
        """
        🔧 Analyzer 호출
        - UserFetcher 제거됨 → id 외의 유저 정보 사용 없음
        - relations 제거됨 → 빈 리스트 전달
        """
        if self.verbose:
            print("\n🧮 [Analyzer] 대화 분석 중...")
            print(f"   → 분석 대상 사용자 ID: {state.id}")

        result = self.analyzer.analyze(
            conversation_df=state.conversation_df,
            relations=[],             
            id=state.id,
        )

        state.analysis_result = result
        print(f"   → 분석 완료: Score={result.get('score')}")

        return state

    def node_save(self, state: AnalysisState):
        """
        🔧 분석 결과 DB 저장
        """
        if self.verbose:
            print("\n💾 [AnalysisSaver] 분석 결과 DB 저장 중...")

        saved = self.saver.save(state.db, state.analysis_result, state)
        print(f"   → 저장 결과: {saved.get('status')}")

        return state

    # =====================================
    # 실행 함수
    # =====================================
    def run(self, db: Session, conversation_df: pd.DataFrame, id: int, conv_id: str):
        """
        🔧 DB 세션 및 대화 DataFrame을 입력받아 최소 파이프라인 실행
        """
        if self.verbose:
            print("\n🚀 [AnalysisGraph] 파이프라인 실행 시작")
            print("=" * 60)

        state = AnalysisState(
            db=db,
            conversation_df=conversation_df,
            id=id,
            conv_id=conv_id,
            verbose=self.verbose,
        )

        result_state = self.pipeline.invoke(state)

        if self.verbose:
            print("\n✅ [AnalysisGraph] 파이프라인 실행 완료")
            print("=" * 60)

        return result_state
