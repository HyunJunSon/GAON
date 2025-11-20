from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
import pandas as pd
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

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
# ✅ State 정의 (DB 세션 추가)
# =====================================
@dataclass
class AnalysisState:
    # ✅ DB 관련
    db: Optional[Session] = None

    # 대화 정보
    conversation_df: Optional[pd.DataFrame] = None
    id: Optional[int] = None
    conv_id: Optional[str] = None

    # ⭐ 새로 추가된 필드
    speaker_segments: List[Dict[str, Any]] = field(default_factory=list)
    user_gender: str = "unknown"
    user_age: int = 0
    user_name: Optional[str] = None
    user_speaker_label: str = "SPEAKER_0A"
    other_speaker_label: str = "SPEAKER_0B"
    other_display_name: str = "상대방"

    # 분석 결과
    family_info: Optional[Dict[str, Any]] = None
    relations: Optional[List[Dict[str, Any]]] = None
    analysis_result: Optional[Dict[str, Any]] = None

    # 검증 상태
    validated: bool = False
    meta: Dict[str, Any] = field(default_factory=dict)
    verbose: bool = True


# =====================================
# ✅ Graph 설계 (DB 연동)
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
        self.saver = AnalysisSaver(verbose)  # 🔧 verbose 전달

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
            if not state.family_info or not state.family_info.get("has_family"):
                return "resolve_llm"
            return "resolve_db"

        self.graph.add_conditional_edges("check_family", family_condition)
        self.graph.add_edge("resolve_db", "analyze")
        self.graph.add_edge("resolve_llm", "analyze")
        self.graph.add_edge("analyze", "save")
        self.graph.add_edge("save", END)

        self.pipeline = self.graph.compile()

    # =====================================
    # ✅ 노드 함수들 (DB 세션 사용)
    # =====================================

    def node_fetch_user(self, state: AnalysisState):
        """
        ✅ DB에서 사용자 정보 조회
        """
        if self.verbose:
            print("\n👤 [UserFetcher] DB에서 사용자 정보 조회 중...")

        if state.db is None:
            raise ValueError("❌ DB 세션이 없습니다!")

        user_info = self.userfetcher.fetch(state.db, state)
        state.family_info = user_info

        print(f"   → 사용자: {user_info.get('user_name')}")
        return state

    def node_check_family(self, state: AnalysisState):
        """
        ✅ 가족 관계 확인
        """
        if self.verbose:
            print("\n👪 [FamilyChecker] 가족 관계 확인 중...")

        has_family, fam_id = self.familychecker.check(state.db, state.family_info)

        if has_family:
            state.family_info["has_family"] = True
            state.family_info["fam_id"] = fam_id
            print(f"   ✅ 가족 ID: {fam_id}")
        else:
            state.family_info["has_family"] = False
            print("   ⚠️ 가족 정보 없음 → LLM 추론 경로")

        return state

    def node_resolve_db(self, state: AnalysisState):
        """
        ✅ DB 기반 가족 관계 조회
        """
        if self.verbose:
            print("\n📇 [RelationResolver_DB] DB 기반 가족 관계 조회 중...")

        fam_id = state.family_info.get("fam_id")
        relations = self.dbresolver.resolve(state.db, fam_id)
        state.relations = relations

        print(f"   → DB 관계자 수: {len(relations)}명")
        return state

    def node_resolve_llm(self, state: AnalysisState):
        """
        ✅ LLM 기반 관계 추론
        """
        if self.verbose:
            print("\n🧠 [RelationResolver_LLM] LLM 기반 관계 추론 중...")

        state.relations = self.llmresolver.resolve(state.conversation_df)

        print(f"   → 추론된 관계: {len(state.relations)}명")
        return state

    def node_analyze(self, state: AnalysisState):
        """
        ✅ 감정·스타일 분석 수행 (사용자 중심)
        """
        if self.verbose:
            print("\n🧮 [Analyzer] 감정·스타일 분석 수행 중...")
            print(f"   👤 분석 대상 사용자: {state.id}")

        result = self.analyzer.analyze(
            speaker_segments=state.speaker_segments,
            user_id=state.id,
            user_gender=state.user_gender,
            user_age=state.user_age,
            user_name=state.user_name,
            user_speaker_label=state.user_speaker_label,
            other_speaker_label=state.other_speaker_label,
            other_display_name=state.other_display_name
        )

        state.analysis_result = result

        print(f"   ✅ 분석 완료: score={result.get('score', 0):.2f}")
        return state

    def node_save(self, state: AnalysisState):
        """
        ✅ 분석 결과 DB 저장
        """
        if self.verbose:
            print("\n💾 [AnalysisSaver] 분석 결과 DB 저장 중...")

        saved = self.saver.save(state.db, state.analysis_result, state)

        print(f"   ✅ 저장: {saved.get('status')}")
        return state

    # =====================================
    # ✅ 실행 메서드 (DB 세션 주입)
    # =====================================
    def run(
        self, 
        db: Session, 
        conv_id: str,
        speaker_segments: List[Dict[str, Any]],
        user_id: int,
        user_gender: str = "unknown",
        user_age: int = 0,
        user_name: str = None,
        user_speaker_label: str = "SPEAKER_0A",
        other_speaker_label: str = "SPEAKER_0B",
        other_display_name: str = "상대방",
        conversation_df: pd.DataFrame = None  # 하위 호환성
    ):
        """
        ✅ Analysis 파이프라인 실행 (DB 연동)
        """
        if self.verbose:
            print("\n🚀 [AnalysisGraph] 실행 시작\n" + "=" * 60)

        # ✅ 초기 상태 생성
        # conversation_df가 없으면 speaker_segments로 생성
        if conversation_df is None and speaker_segments:
            import pandas as pd
            conversation_df = pd.DataFrame(speaker_segments)
        
        state = AnalysisState(
            db=db,
            conversation_df=conversation_df,
            id=user_id,
            conv_id=conv_id,
            speaker_segments=speaker_segments,
            user_gender=user_gender,
            user_age=user_age,
            user_name=user_name,
            user_speaker_label=user_speaker_label,
            other_speaker_label=other_speaker_label,
            other_display_name=other_display_name,
            verbose=self.verbose,
        )

        # ✅ 파이프라인 실행
        result_state = self.pipeline.invoke(state)

        if self.verbose:
            print("\n✅ [AnalysisGraph] 파이프라인 실행 완료\n" + "=" * 60)

        return result_state
