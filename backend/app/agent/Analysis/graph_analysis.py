# =========================================
# app/agent/Analysis/graph_analysis.py (FINAL)
# =========================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
import pandas as pd

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

# Stage Modules
from .nodes import (
    Analyzer,                # Stage 1~6
    SafetyLLMAnalyzer,       # Stage 7
    SummaryBuilder,          # Stage 8
    TemperatureScorer,       # Stage 9
    AnalysisSaver            # SAVE
)

from app.agent.crud import get_user_by_id


# =========================================
# ⭐ AnalysisState
# =========================================
@dataclass
class AnalysisState:
    db: Optional[Session] = None
    conv_id: Optional[str] = None
    user_id: Optional[int] = None

    # Cleaner Output
    speaker_segments: Optional[List[Dict[str, Any]]] = None
    user_gender: Optional[str] = None
    user_age: Optional[int] = None

    # Stage internal data
    df: Optional[pd.DataFrame] = None
    user_speaker_label: Optional[str] = None

    # Stage results
    statistics: Dict[str, Any] = field(default_factory=dict)
    prosody_norm: Dict[str, Any] = field(default_factory=dict)
    surrogate: Dict[str, Any] = field(default_factory=dict)
    trigger: Dict[str, Any] = field(default_factory=dict)
    style_analysis: Dict[str, Any] = field(default_factory=dict)
    summary: Optional[str] = None
    temperature_score: Optional[float] = None

    validated: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)
    verbose: bool = True


# =========================================
# 🧠 AnalysisGraph
# =========================================
class AnalysisGraph:
    def __init__(self, verbose=True):
        self.verbose = verbose

        # Stage modules
        self.analyzer = Analyzer(verbose)
        self.llm_analyzer = SafetyLLMAnalyzer()
        self.summary_builder = SummaryBuilder()
        self.temp_scorer = TemperatureScorer()
        self.saver = AnalysisSaver(verbose)

        # Graph build
        self.graph = StateGraph(AnalysisState)

        # Nodes
        self.graph.add_node("analyze_features", self.node_analyze_features)
        self.graph.add_node("llm_style", self.node_llm_style)
        self.graph.add_node("build_summary", self.node_summary)
        self.graph.add_node("temperature", self.node_temperature)
        self.graph.add_node("save", self.node_save)

        # Flow
        self.graph.set_entry_point("analyze_features")
        self.graph.add_edge("analyze_features", "llm_style")
        self.graph.add_edge("llm_style", "build_summary")
        self.graph.add_edge("build_summary", "temperature")
        self.graph.add_edge("temperature", "save")
        self.graph.add_edge("save", END)

        self.pipeline = self.graph.compile()


    # =========================================
    # Stage 1~6 Analyzer
    # =========================================
    def node_analyze_features(self, state: AnalysisState):
        if state.verbose:
            print("\n🧮 [Stage 1~6] 텍스트·음향 Feature 분석 중...")

        result = self.analyzer.analyze(
            speaker_segments=state.speaker_segments,
            user_id=state.user_id,
            user_gender=state.user_gender,
            user_age=state.user_age
        )

        state.statistics = result["statistics"]
        state.prosody_norm = result["prosody_norm"]
        state.surrogate = result["surrogate"]
        state.trigger = result["trigger"]
        state.df = result["df"]
        state.user_speaker_label = result["user_speaker_label"]

        return state


    # =========================================
    # Stage 7 LLM Style Analysis
    # =========================================
    def node_llm_style(self, state: AnalysisState):
        if state.verbose:
            print("\n🧠 [Stage 7] LLM 기반 스타일 분석 중...")

        style_json = self.llm_analyzer.analyze(
            df=state.df,
            user_speaker_label=state.user_speaker_label,
            user_gender=state.user_gender,
            user_age=state.user_age,
            stats=state.statistics,
            prosody_norm=state.prosody_norm,
            surrogate=state.surrogate,
            trigger=state.trigger
        )

        state.style_analysis = style_json
        return state


    # =========================================
    # Stage 8 Summary
    # =========================================
    def node_summary(self, state: AnalysisState):
        if state.verbose:
            print("\n📝 [Stage 8] Summary 생성 중...")

        # 사용자 정보 조회
        user = get_user_by_id(state.db, state.user_id)
        username = user.get("user_name", "사용자")

        summary = self.summary_builder.build(
            user_name=username,
            style=state.style_analysis,
            statistics=state.statistics,
            prosody_norm=state.prosody_norm
        )

        state.summary = summary
        return state


    # =========================================
    # Stage 9 Temperature Score
    # =========================================
    def node_temperature(self, state: AnalysisState):
        if state.verbose:
            print("\n🔥 [Stage 9] Temperature Score 계산 중...")

        score = self.temp_scorer.score(
            style=state.style_analysis,
            prosody_norm=state.prosody_norm,
            trigger=state.trigger
        )

        state.temperature_score = score
        return state


    # =========================================
    # Stage 10 Save to DB
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

        saved = self.saver.save(
            db=state.db,
            result=result,
            conv_id=state.conv_id,
            user_id=state.user_id,
            conversation_count=len(state.df)
        )

        state.meta["analysis_id"] = saved.get("analysis_id")
        state.validated = True
        return state


    # =========================================
    # Run Entire Pipeline
    # =========================================
    def run(
        self,
        db: Session,
        conv_id: str,
        speaker_segments: List[Dict[str, Any]],
        user_id: int,
        user_gender: str,
        user_age: int,
        verbose=True,
    ):

        if verbose:
            print("\n🚀 [AnalysisGraph] 파이프라인 시작")
            print("=" * 60)

        state = AnalysisState(
            db=db,
            conv_id=conv_id,
            user_id=user_id,
            speaker_segments=speaker_segments,
            user_gender=user_gender,
            user_age=user_age,
            verbose=verbose
        )

        output = self.pipeline.invoke(state)
        final_state = output.get("__state__", state)

        if verbose:
            print("\n✅ [AnalysisGraph] 완료")
            print("=" * 60)

        return final_state
