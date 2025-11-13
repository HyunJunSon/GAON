# app/agent/Cleaner/graph_cleaner.py

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
import pandas as pd

# 노드 import
from .nodes import (
    RawFetcher,       # 원문(raw_content) 불러오기
    DataInspector,    # turn ≥ 3
    TokenCounter,     # 화자별 25 어절
    ExceptionHandler  # 예외 처리
)


@dataclass
class CleanerState:
    db: Optional[Session] = None
    conv_id: Optional[str] = None

    raw_df: Optional[pd.DataFrame] = None
    inspected_df: Optional[pd.DataFrame] = None

    # 결과 및 검증 관련
    validated: bool = False
    issues: List[str] = field(default_factory=list)

    verbose: bool = False


# =========================================
class CleanerGraph:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose

        # 🔧 필요한 노드 초기화
        self.fetcher = RawFetcher()
        self.inspector = DataInspector()
        self.token_counter = TokenCounter()
        self.exception_handler = ExceptionHandler()

        # 🔧 그래프 정의
        self.graph = StateGraph(CleanerState)
        self.graph.add_node("fetch", self.node_fetch)
        self.graph.add_node("inspect", self.node_inspect)
        self.graph.add_node("tokenize", self.node_tokenize)

        # 흐름 정의
        self.graph.set_entry_point("fetch")
        self.graph.add_edge("fetch", "inspect")

        # 🔧 조건부: inspect → tokenize or END
        def inspect_cond(state: CleanerState):
            return "tokenize" if not state.issues else END

        self.graph.add_conditional_edges("inspect", inspect_cond)

        # 🔧 조건부: tokenize → END
        def tokenize_cond(state: CleanerState):
            return END

        self.graph.add_conditional_edges("tokenize", tokenize_cond)

        self.pipeline = self.graph.compile()

    # =========================================
    # 1️⃣ RawFetcher
    # =========================================
    def node_fetch(self, state: CleanerState):
        if self.verbose:
            print("\n[1️⃣ RawFetcher] 원문(raw_content) 불러오는 중…")

        try:
            state.raw_df = self.fetcher.fetch(
                db=state.db,
                conv_id=state.conv_id
            )
            print(f"   → 발화 {len(state.raw_df)}개 로드 완료")
            return state
        except Exception as e:
            return self.exception_handler.handle(e)

    # =========================================
    # 2️⃣ DataInspector (turn ≥ 3 검사)
    # =========================================
    def node_inspect(self, state: CleanerState):
        if self.verbose:
            print("\n[2️⃣ DataInspector] 발화 turn 검사 중…")

        try:
            inspected_df, issues = self.inspector.inspect(state.raw_df, state)
            state.inspected_df = inspected_df
            state.issues.extend(issues)

            if issues:
                print(f"   ❌ 검사 실패: {issues}")
            else:
                print("   ✅ turn 검사 통과")

            return state
        except Exception as e:
            return self.exception_handler.handle(e)

    # =========================================
    # 3️⃣ TokenCounter (화자별 어절 ≥ 25 검사)
    # =========================================
    def node_tokenize(self, state: CleanerState):
        if self.verbose:
            print("\n[3️⃣ TokenCounter] 화자별 어절 수 검사 중…")

        try:
            df, issues = self.token_counter.count(state.inspected_df, state)
            state.issues.extend(issues)

            if issues:
                print(f"   ❌ 어절 부족: {issues}")
            else:
                print("   ✅ 화자별 어절 수 조건 통과")

            return state
        except Exception as e:
            return self.exception_handler.handle(e)

    # =========================================
    # 실행 메서드
    # =========================================
    def run(self, db: Session, conv_id: str):
        if self.verbose:
            print("\n🚀 [CleanerGraph] 실행 시작\n" + "=" * 60)

        state = CleanerState(
            db=db,
            conv_id=conv_id,
            verbose=self.verbose,
        )

        final_state = self.pipeline.invoke(state)

        if self.verbose:
            print("🏁 [CleanerGraph] 실행 종료\n" + "=" * 60)

        return final_state
