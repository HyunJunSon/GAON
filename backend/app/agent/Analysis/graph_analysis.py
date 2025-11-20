# =========================================
# app/agent/Analysis/graph_analysis.py (PRESENTATION PRINT VERSION)
# =========================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
import pandas as pd

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from .nodes import (
    Analyzer,
    SafetyLLMAnalyzer,
    SummaryBuilder,
    TemperatureScorer,
    AnalysisSaver
)

from app.agent.crud import get_user_by_id


# =========================================
# ⭐ STATE
# =========================================
@dataclass
class AnalysisState:
    db: Optional[Session] = None
    conv_id: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None

    # Input
    speaker_segments: Optional[List[Dict[str, Any]]] = None
    user_gender: Optional[str] = None
    user_age: Optional[int] = None

    # Label from Cleaner
    user_speaker_label: Optional[str] = None
    other_speaker_label: Optional[str] = None
    other_display_name: Optional[str] = None

    # Internal
    df: Optional[pd.DataFrame] = None

    # Results
    statistics: Dict[str, Any] = field(default_factory=dict)
    prosody_norm: Dict[str, Any] = field(default_factory=dict)
    surrogate: Dict[str, Any] = field(default_factory=dict)
    trigger: Dict[str, Any] = field(default_factory=dict)
    style_analysis: Dict[str, Any] = field(default_factory=dict)
    summary: Optional[str] = None
    temperature_score: Optional[float] = None

    validated: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)
    analysis_id: Optional[str] = None


    verbose: bool = True


# =========================================
# 🧠 GRAPH
# =========================================
class AnalysisGraph:
    def __init__(self, verbose=True):
        self.verbose = verbose

        self.analyzer = Analyzer(verbose=False)
        self.llm_analyzer = SafetyLLMAnalyzer()
        self.summary_builder = SummaryBuilder()
        self.temp_scorer = TemperatureScorer()
        self.saver = AnalysisSaver(verbose=False)

        self.graph = StateGraph(AnalysisState)

        self.graph.add_node("analyze_features", self.node_analyze_features)
        self.graph.add_node("llm_style", self.node_llm_style)
        self.graph.add_node("build_summary", self.node_summary)
        self.graph.add_node("temperature", self.node_temperature)
        self.graph.add_node("save", self.node_save)

        self.graph.set_entry_point("analyze_features")
        self.graph.add_edge("analyze_features", "llm_style")
        self.graph.add_edge("llm_style", "build_summary")
        self.graph.add_edge("build_summary", "temperature")
        self.graph.add_edge("temperature", "save")

        self.graph.set_finish_point("save")

        self.pipeline = self.graph.compile()


    # =======================================================
    # Stage 1~6
    # =======================================================
    def node_analyze_features(self, state: AnalysisState):
        result = self.analyzer.analyze(
            speaker_segments=state.speaker_segments,
            user_id=state.user_id,
            user_gender=state.user_gender,
            user_age=state.user_age,
            user_speaker_label=state.user_speaker_label,
            other_speaker_label=state.other_speaker_label,
            other_display_name=state.other_display_name
        )

        state.statistics = result["statistics"]
        state.prosody_norm = result["prosody_norm"]
        state.surrogate = result["surrogate"]
        state.trigger = result["trigger"]
        state.df = result["df"]

        if state.verbose:
            print("\n\n==============================")
            print("📌 [Stage 1~6] Feature 분석 결과")
            print("==============================")
            print("✔ 텍스트 통계:", state.statistics)
            print("✔ Prosody Normalization:", state.prosody_norm)
            print("✔ 관계 Surrogate:", state.surrogate)
            print("✔ Trigger 분석:", state.trigger)

        return state


    # =======================================================
    # Stage 7 LLM Style
    # =======================================================
    def node_llm_style(self, state: AnalysisState):
        if state.verbose:
            print("\n🧠 [Stage 7] LLM 기반 스타일 분석 중...")
            print("  └ df is None?:", state.df is None)

        # LLM이 반환하는 것은 곧바로 style_analysis 딕셔너리
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

        print("  ➤ [DEBUG] LLM 스타일 분석 결과:", style_json)
        state.style_analysis = style_json
        return state


    # =======================================================
    # Stage 8 Summary
    # =======================================================
    def node_summary(self, state: AnalysisState):

        user_name = state.user_name

        result = self.summary_builder.build(
            user_name=user_name,
            df=state.df,                              
            user_speaker_label=state.user_speaker_label,  
            user_gender=state.user_gender,           
            user_age=state.user_age,                  
            style=state.style_analysis,
            statistics=state.statistics,
            prosody_norm=state.prosody_norm,
            surrogate=state.surrogate,
            trigger=state.trigger,
        )

        state.summary = result


        if state.verbose:
            print("\n==============================")
            print("📝 [Stage 8] Summary 생성 결과")
            print("==============================")
            print(state.summary)

        return state


    # =======================================================
    # Stage 9 Temperature Score
    # =======================================================
    def node_temperature(self, state: AnalysisState):

        result = self.temp_scorer.score(
            style=state.style_analysis,
            prosody_norm=state.prosody_norm,
            trigger=state.trigger
        )

        state.temperature_score = result


        if state.verbose:
            print("\n==============================")
            print("🔥 [Stage 9] Temperature Score")
            print("==============================")
            print("✔ Score:", state.temperature_score)

        return state


    # =======================================================
    # Stage 10 SAVE
    # =======================================================
    def node_save(self, state: AnalysisState):

        save_input = {
            "summary": state.summary,
            "style_analysis": state.style_analysis,
            "statistics": state.statistics,
            "temperature_score": state.temperature_score
        }

        saved = self.saver.save(
            db=state.db,
            result=save_input,
            conv_id=state.conv_id,
            user_id=state.user_id,
            conversation_count=len(state.df)
        )

        # save_analysis_result() expected return:
        # { "analysis_id": "...", "validated": True }

        if isinstance(saved, dict):
            # 정상: analysis_id만 저장
            if "analysis_id" in saved:
                state.analysis_id = saved["analysis_id"]

            # validated flag
            state.validated = saved.get("validated", True)

        if state.verbose:
            print("\n==============================")
            print("💾 [Stage 10] 저장 완료")
            print("==============================")
            print("✔ Analysis ID:", state.meta.get("analysis_id"))

        return state


    # =======================================================
    # RUN PIPELINE
    # =======================================================
    def run(
        self,
        db: Session,
        conv_id: str,
        speaker_segments: List[Dict[str, Any]],
        user_id: int,
        user_gender: str,
        user_age: int,
        user_name: str, 
        user_speaker_label: str,
        other_speaker_label: str,
        other_display_name: str,
        verbose=True,
    ):

        if verbose:
            print("\n============================================================")
            print("🚀 [AnalysisGraph] 실행 시작")
            print("============================================================")

        state = AnalysisState(
            db=db,
            conv_id=conv_id,
            user_id=user_id,
            speaker_segments=speaker_segments,
            user_gender=user_gender,
            user_age=user_age,
            user_name=user_name, 
            user_speaker_label=user_speaker_label,
            other_speaker_label=other_speaker_label,
            other_display_name=other_display_name,
            verbose=verbose
        )

        output = self.pipeline.invoke(state)
        return output
