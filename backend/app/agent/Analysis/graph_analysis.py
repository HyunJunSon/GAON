# =========================================
# app/agent/Analysis/graph_analysis.py
# =========================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
import pandas as pd

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

# 🔧 Stage별 모듈 import
from .nodes import (
    Analyzer,                # Stage 1~6
    SafetyLLMAnalyzer,       # Stage 7
    SummaryBuilder,          # Stage 8
    TemperatureScorer,       # Stage 9
    AnalysisSaver            # Save → DB
)

from app.agent.crud import get_user_by_id


# =========================================
# ⭐ NEW — AnalysisState 확장
# =========================================
@dataclass
class AnalysisState:
    db: Optional[Session] = None

    conv_id: Optional[str] = None
    id: Optional[int] = None

    conversation_df: Optional[pd.DataFrame] = None
    text_features: Dict[str, Any] = field(default_factory=dict)    
    audio_features: Dict[str, Any] = field(default_factory=dict)  

    # Stage별 결과 저장
    statistics: Dict[str, Any] = field(default_factory=dict)
    audio_normalization: Dict[str, Any] = field(default_factory=dict)
    trigger_info: Dict[str, Any] = field(default_factory=dict)
    surrogate: Dict[str, Any] = field(default_factory=dict)

    style_analysis: Dict[str, Any] = field(default_factory=dict)
    summary: Optional[str] = None
    temperature_score: Optional[float] = None

    analysis_result: Optional[Dict[str, Any]] = None

    validated: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)

    verbose: bool = True


# =========================================
# 🏗️ AnalysisGraph 재작성
# =========================================
class AnalysisGraph:
    def __init__(self, verbose=True):
        self.verbose = verbose

        # Stage 모듈 준비
        self.analyzer = Analyzer(verbose)
        self.llm_analyzer = SafetyLLMAnalyzer()
        self.summary_builder = SummaryBuilder()
        self.temp_scorer = TemperatureScorer()
        self.saver = AnalysisSaver(verbose)

        # Graph 빌드
        self.graph = StateGraph(AnalysisState)

        # Node 등록
        self.graph.add_node("analyze_features", self.node_analyze_features)
        self.graph.add_node("llm_style", self.node_llm_style)
        self.graph.add_node("build_summary", self.node_summary)
        self.graph.add_node("temperature", self.node_temperature)
        self.graph.add_node("save", self.node_save)

        # Entry & edges
        self.graph.set_entry_point("analyze_features")

        self.graph.add_edge("analyze_features", "llm_style")
        self.graph.add_edge("llm_style", "build_summary")
        self.graph.add_edge("build_summary", "temperature")
        self.graph.add_edge("temperature", "save")
        self.graph.add_edge("save", END)

        self.pipeline = self.graph.compile()


    # =========================================
    # Stage 1~6: Analyzer (텍스트+음향 변환)
    # =========================================
    def node_analyze_features(self, state: AnalysisState):
        if state.verbose:
            print("\n🧮 [Stage 1~6] 텍스트·음향 Feature 분석 중...")

        result = self.analyzer.analyze(
            df=state.conversation_df,
            id=state.id,
            text_features=state.text_features,     
            audio_features=state.audio_features
        )

        state.statistics = result["statistics"]
        state.audio_normalization = result["prosody_norm"]
        state.surrogate = result["surrogate"]
        state.trigger_info = result["trigger"]

        return state


    # =========================================
    # Stage 7: LLM 스타일 분석
    # =========================================
    def node_llm_style(self, state: AnalysisState):
        if state.verbose:
            print("\n🧠 [Stage 7] LLM 기반 스타일 분석 중...")

        style_json = self.llm_analyzer.analyze(
            merged_df=state.conversation_df,
            id=state.id,
            stats=state.statistics,
            prosody_norm=state.audio_normalization,
            surrogate=state.surrogate,
            trigger=state.trigger_info
        )

        state.style_analysis = style_json
        return state


    # =========================================
    # Stage 8: Summary Insight 생성
    # =========================================
    def node_summary(self, state: AnalysisState):
        if state.verbose:
            print("\n📝 [Stage 8] Summary Insight 생성 중...")

        # 사용자 이름 조회
        user = get_user_by_id(state.db, state.id)
        user_name = user.get("user_name", "사용자")

        # 🟡 MODIFIED: SummaryBuilder.build 인자 이름/개수 맞게 수정
        summary = self.summary_builder.build(
            user_name=user_name,
            style=state.style_analysis,             
            statistics=state.statistics,             
            prosody_norm=state.audio_normalization 
        )

        state.summary = summary
        return state


    # =========================================
    # Stage 9: Temperature Score 계산
    # =========================================
    def node_temperature(self, state: AnalysisState):
        if state.verbose:
            print("\n🔥 [Stage 9] Temperature Score 계산 중...")

        score = self.temp_scorer.score(
        style=state.style_analysis,
        statistics=state.statistics,
        prosody_norm=state.audio_normalization,
        trigger_info=state.trigger_info
    )

        state.temperature_score = score
        return state


    # =========================================
    # Stage 10: DB 저장
    # =========================================
    def node_save(self, state: AnalysisState):
        if state.verbose:
            print("\n💾 [SAVE] 분석 결과 저장 중...")

        result = {
            "summary": state.summary,
            "style_analysis": state.style_analysis,
            "statistics": state.statistics,
            "temperature_score": state.temperature_score
        }

        saved = self.saver.save(state.db, result, state)
        state.meta["analysis_id"] = saved.get("analysis_id")
        state.validated = True

        return state


    # =========================================
    # 실행
    # =========================================
    def run(self, db: Session, conversation_df: pd.DataFrame,
            audio_features: List[Dict], id: int, conv_id: str):

        if self.verbose:
            print("\n🚀 [AnalysisGraph] 파이프라인 실행 시작")
            print("="*60)

        state = AnalysisState(
            db=db,
            conversation_df=conversation_df,
            audio_features=audio_features,
            id=id,
            conv_id=conv_id,
            verbose=self.verbose
        )

        output_dict = self.pipeline.invoke(state)

        final_state = output_dict["__state__"] if "__state__" in output_dict else state

        if self.verbose:
            print("\n✅ [AnalysisGraph] 파이프라인 실행 완료")
            print("="*60)

        return final_state
