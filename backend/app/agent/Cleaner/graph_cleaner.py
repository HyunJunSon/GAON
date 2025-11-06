from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
from langgraph.graph import StateGraph, END
from .nodes import (
    RawFetcher,
    RawInspector,
    ConversationCleaner,
    ExceptionHandler,
    ConversationValidator,
    ConversationSaver,
)
try:
    import pandas as pd
except Exception:
    pd = None


# =========================================
# ✅ 상태 정의
# =========================================
@dataclass
class CleanerState:
    raw_df: Optional[pd.DataFrame] = None
    created_at: Optional[str] = None
    context: Optional[str] = None
    user_id: Optional[str] = None               # ✅ 업로더
    user_ids: List[str] = field(default_factory=list)  # ✅ 전체 참여자
    inspected_df: Optional[pd.DataFrame] = None
    cleaned_df: Optional[pd.DataFrame] = None
    validated: bool = False
    saved: bool = False
    issues: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    verbose: bool = False


# =========================================
# ✅ 그래프 정의
# =========================================
class CleanerGraph:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.fetcher = RawFetcher()
        self.inspector = RawInspector()
        self.cleaner = ConversationCleaner(verbose=verbose)
        self.validator = ConversationValidator(verbose=verbose)
        self.saver = ConversationSaver()
        self.exception_handler = ExceptionHandler()

        self.graph = StateGraph(CleanerState)
        self.graph.add_node("fetch", self.node_fetch)
        self.graph.add_node("inspect", self.node_inspect)
        self.graph.add_node("clean", self.node_clean)
        self.graph.add_node("validate", self.node_validate)
        self.graph.add_node("save", self.node_save)

        self.graph.set_entry_point("fetch")
        self.graph.add_edge("fetch", "inspect")

        def inspection_condition(state: CleanerState):
            return "clean" if not state.issues else END
        self.graph.add_conditional_edges("inspect", inspection_condition)

        def validation_condition(state: CleanerState):
            return "save" if state.validated else END
        self.graph.add_conditional_edges("validate", validation_condition)

        self.graph.add_edge("clean", "validate")
        self.graph.add_edge("save", END)
        self.pipeline = self.graph.compile()

    def node_fetch(self, state: CleanerState):
        if self.verbose:
            print("\n[1️⃣ RawFetcher] Fetching raw data…")
        state.raw_df = self.fetcher.fetch(sample=True)
        return state

    def node_inspect(self, state: CleanerState):
        if self.verbose:
            print("\n[2️⃣ RawInspector] Inspecting raw data…")
        inspected_df, issues = self.inspector.inspect(state.raw_df, state)
        state.inspected_df = inspected_df
        state.issues.extend(issues)
        if issues:
            print("   ⚠️ Issues detected:", issues)
        return state

    def node_clean(self, state: CleanerState):
        if self.verbose:
            print("\n[3️⃣ ConversationCleaner] Cleaning text with LLM…")
        state.cleaned_df = self.cleaner.clean(state.inspected_df, state)
        return state

    def node_validate(self, state: CleanerState):
        if self.verbose:
            print("\n[4️⃣ ConversationValidator] Evaluating conversation validity…")
        validated, issues = self.validator.validate(state.cleaned_df, state)
        state.validated = validated
        state.issues.extend(issues)
        print(f"   ✅ Validated: {validated}, Issues: {issues}")
        return state

    def node_save(self, state: CleanerState):
        if self.verbose:
            print("\n[5️⃣ ConversationSaver] Saving conversation result…")
        result = self.saver.save(state.cleaned_df, state)
        print(f"   💾 Saved: {result}")
        return state

    def run(self, **kwargs):
        state = CleanerState(
            verbose=self.verbose,
            user_id="201",
            context="샘플 대화 context",
            created_at="2025-11-05 12:00:00",
        )

        print("\n🚀 [CleanerGraph] 실행 시작\n" + "=" * 60)
        # ✅ stream 대신 invoke로 변경 — invoke는 최종 state를 반환
        result_state = self.pipeline.invoke(state)
        
        if self.verbose:
            print("✅ [CleanerGraph] 파이프라인 실행 완료\n" + "=" * 60)

        # ✅ CleanerState로 래핑 (혹시 dict 형태로 리턴될 경우 대비)
        if isinstance(result_state, dict):
            result_state = CleanerState(**result_state)

        return result_state

