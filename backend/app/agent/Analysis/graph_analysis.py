# app/agent/Analysis/graph_analysis.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
import pandas as pd
from langgraph.graph import StateGraph, END

from .nodes import (
    UserFetcher,
    FamilyChecker,
    RelationResolver_DB,
    RelationResolver_LLM,
    Analyzer,
    ScoreEvaluator,
    AnalysisSaver,
)

# =====================================
# ✅ State 정의
# =====================================
@dataclass
class AnalysisState:
    conversation_df: Optional[pd.DataFrame] = None
    user_id: Optional[str] = None
    conv_id: Optional[str] = None
    family_info: Optional[Dict[str, Any]] = None
    relations: Optional[List[Dict[str, Any]]] = None
    analysis_result: Optional[Dict[str, Any]] = None
    validated: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)
    verbose: bool = True

# =====================================
# ✅ Graph 설계
# =====================================
class AnalysisGraph:
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.userfetcher = UserFetcher()
        self.familychecker = FamilyChecker()
        self.dbresolver = RelationResolver_DB()
        self.llmresolver = RelationResolver_LLM(verbose)
        self.analyzer = Analyzer(verbose)
        self.evaluator = ScoreEvaluator()
        self.saver = AnalysisSaver()

        self.graph = StateGraph(AnalysisState)
        self.graph.add_node("fetch_user", self.node_fetch_user)
        self.graph.add_node("check_family", self.node_check_family)
        self.graph.add_node("resolve_db", self.node_resolve_db)
        self.graph.add_node("resolve_llm", self.node_resolve_llm)
        self.graph.add_node("analyze", self.node_analyze)
        self.graph.add_node("save", self.node_save)

        self.graph.set_entry_point("fetch_user")
        self.graph.add_edge("fetch_user", "check_family")

        def family_condition(state: AnalysisState):
            if not state.family_info:
                return "resolve_llm"
            return "resolve_db"

        self.graph.add_conditional_edges("check_family", family_condition)
        self.graph.add_edge("resolve_db", "analyze")
        self.graph.add_edge("resolve_llm", "analyze")
        self.graph.add_edge("analyze", "save")
        self.graph.add_edge("save", END)

        self.pipeline = self.graph.compile()

    # -------------------------------------
    # 노드 함수들
    # -------------------------------------
    def node_fetch_user(self, state: AnalysisState):
        if self.verbose:
            print("\n👤 [UserFetcher] 사용자 정보 조회 중...")
        user_info = self.userfetcher.fetch(state)
        state.family_info = user_info
        print(f"   → 사용자 정보: {user_info}")
        return state

    def node_check_family(self, state: AnalysisState):
        if self.verbose:
            print("\n👪 [FamilyChecker] 가족 관계 확인 중...")
        has_family, fam_id = self.familychecker.check(state.family_info)
        if has_family:
            state.family_info["fam_id"] = fam_id
            print(f"   ✅ 가족 ID: {fam_id}")
        else:
            print("   ⚠️ 가족 정보 없음 → LLM 추론 경로로 전환")
            state.family_info = None
        return state

    def node_resolve_db(self, state: AnalysisState):
        if self.verbose:
            print("\n📇 [RelationResolver_DB] DB 기반 가족 관계 조회 중...")
        fam_id = state.family_info.get("fam_id")
        relations = self.dbresolver.resolve(fam_id)
        state.relations = relations
        print(f"   → DB 관계자 수: {len(relations)}명")
        return state

    def node_resolve_llm(self, state: AnalysisState):
        if self.verbose:
            print("\n🧠 [RelationResolver_LLM] LLM 기반 관계 추론 중...")
        state.relations = self.llmresolver.resolve(state.conversation_df)
        print(f"   → 추론된 관계: {state.relations}")
        return state

    def node_analyze(self, state: AnalysisState):
        if self.verbose:
            print("\n🧮 [Analyzer] 감정·스타일 분석 수행 중...")
        result = self.analyzer.analyze(state.conversation_df, state.relations)
        state.analysis_result = result
        return state

    def node_save(self, state: AnalysisState):
        if self.verbose:
            print("\n💾 [AnalysisSaver] 분석 결과 저장 중...")
        saved = self.saver.save(state.analysis_result, state)
        print(f"   ✅ 저장 완료: {saved}")
        return state

    def run(self, conversation_df, user_id="201", conv_id="C001"):
        state = AnalysisState(conversation_df=conversation_df, user_id=user_id, conv_id=conv_id)
        return self.pipeline.invoke(state)
