# app/agent/Cleaner/graph_cleaner.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from .nodes import (
    RawFetcher,
    RawInspector,
    ConversationCleaner,
    ExceptionHandler,
    ConversationValidator,
    ConversationSaver,
)
import pandas as pd



# =========================================
# ✅ 상태 정의 (DB 세션 추가)
# =========================================
@dataclass
class CleanerState:
    # ✅ DB 관련
    db: Optional[Session] = None              # SQLAlchemy 세션
    conv_id: Optional[str] = None             # 대화 UUID (PK)

    # DataFrame 관련
    raw_df: Optional[pd.DataFrame] = None
    inspected_df: Optional[pd.DataFrame] = None
    cleaned_df: Optional[pd.DataFrame] = None

    # 메타데이터
    create_date: Optional[str] = None
    context: Optional[str] = None
    id: Optional[str] = None             #  user_ids: List[str] = field(default_factory=list)  # 전체 참여자

    # 검증 상태
    validated: bool = False
    saved: bool = False
    issues: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    verbose: bool = False


# =========================================
# ✅ 그래프 정의 (DB 연동)
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

        # 그래프 정의
        self.graph = StateGraph(CleanerState)
        self.graph.add_node("fetch", self.node_fetch)
        self.graph.add_node("inspect", self.node_inspect)
        self.graph.add_node("clean", self.node_clean)
        self.graph.add_node("validate", self.node_validate)
        self.graph.add_node("save", self.node_save)

        # 실행 흐름 연결
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

    # =========================================
    # ✅ 노드 함수들 (DB 세션 사용)
    # =========================================
    
    def node_fetch(self, state: CleanerState):
        """
        ✅ DB에서 conversation 조회
        - 변경 전: pk_id 또는 conv_id로 조회
        - 변경 후: conv_id(UUID)로만 조회
        """
        if self.verbose:
            print("\n[1️⃣ RawFetcher] DB에서 대화 조회 중…")

        if state.db is None:
            raise ValueError("❌ DB 세션이 없습니다!")

        if not state.conv_id:
            raise ValueError("❌ conv_id가 필요합니다! (PK 기준)")

        # ✅ RawFetcher 호출
        state.raw_df = self.fetcher.fetch(
            db=state.db,
            conv_id=state.conv_id
        )

        print(f"   ✅ 대화 로드 완료: {len(state.raw_df)}개 발화")
        return state

    def node_inspect(self, state: CleanerState):
        if self.verbose:
            print("\n[2️⃣ RawInspector] 대화 검증 중…")
        inspected_df, issues = self.inspector.inspect(state.raw_df, state)
        state.inspected_df = inspected_df
        state.issues.extend(issues)
        if issues:
            print(f"   ⚠️ 검증 이슈: {issues}")
        else:
            print(f"   ✅ 검증 통과")
        return state

    def node_clean(self, state: CleanerState):
        if self.verbose:
            print("\n[3️⃣ ConversationCleaner] LLM 기반 텍스트 정제 중…")
        state.cleaned_df = self.cleaner.clean(state.inspected_df, state)
        print(f"   ✅ 정제 완료")
        return state

    def node_validate(self, state: CleanerState):
        if self.verbose:
            print("\n[4️⃣ ConversationValidator] 분석 가능성 평가 중…")
        validated, issues = self.validator.validate(state.cleaned_df, state)
        state.validated = validated
        state.issues.extend(issues)
        if validated:
            print(f"   ✅ 분석 가능: 대화 품질 통과")
        else:
            print(f"   ❌ 분석 불가: {issues}")
        return state

    def node_save(self, state: CleanerState):
        if self.verbose:
            print("\n[5️⃣ ConversationSaver] 저장 확인 중…")
        result = self.saver.save(state.cleaned_df, state)
        print(f"   💾 상태: {result.get('status')}")
        return state

    # =========================================
    # ✅ 실행 메서드 (DB 세션 주입)
    # =========================================
    def run(self, db: Session, conv_id: str, id: Optional[str] = None):
        """
        ✅ Cleaner 파이프라인 실행 (DB 연동)
        
        Args:
            db: SQLAlchemy 세션
            conv_id: 대화 UUID ( id: 업로더 ID (선택)
        
        Returns:
            CleanerState (최종 상태)
        """
        if self.verbose:
            print("\n🚀 [CleanerGraph] 실행 시작\n" + "=" * 60)

        # ✅ 초기 상태 생성
        state = CleanerState(
            db=db,
            conv_id=conv_id, id=id,
            verbose=self.verbose,
        )

        # ✅ 파이프라인 실행
        result_state = self.pipeline.invoke(state)

        if self.verbose:
            print("✅ [CleanerGraph] 파이프라인 실행 완료\n" + "=" * 60)

        if isinstance(result_state, dict):
            result_state = CleanerState(**result_state)

        return result_state
