# ============================================
# app/agent/Cleaner/graph_cleaner.py  (FINAL)
# ============================================

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
import pandas as pd

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from .nodes import (
    RawFetcher,
    DataInspector,
    TokenCounter,
    AudioFeatureExtractor,
    ExceptionHandler,
)


# ============================================================
# ⭐ Cleaner STATE
# ============================================================
@dataclass
class CleanerState:
    db: Optional[Session] = None
    conv_id: Optional[str] = None

    # RawFetcher 결과
    df: Optional[pd.DataFrame] = None
    speaker_segments: Optional[List[Dict]] = None
    speaker_mapping: Optional[Dict] = None
    audio_url: Optional[str] = None

    # user 정보
    user_self_id: Optional[int] = None
    user_gender: Optional[str] = None
    user_age: Optional[int] = None
    user_name: Optional[str] = None

    # Processing
    inspected_df: Optional[pd.DataFrame] = None
    audio_segments_with_features: Optional[List[Dict]] = None

    # 상태
    issues: List[str] = field(default_factory=list)
    validated: bool = False
    verbose: bool = False


# ============================================================
# ⭐ CleanerGraph (FINAL)
# ============================================================
class CleanerGraph:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose

        # Nodes
        self.fetcher = RawFetcher()
        self.inspector = DataInspector()
        self.token_counter = TokenCounter()
        self.audio_extractor = AudioFeatureExtractor()
        self.exception_handler = ExceptionHandler()

        # Graph 정의
        self.graph = StateGraph(CleanerState)

        self.graph.add_node("fetch", self.node_fetch)
        self.graph.add_node("inspect", self.node_inspect)
        self.graph.add_node("tokenize", self.node_tokenize)
        self.graph.add_node("audio_extract", self.node_audio_extract)

        # Flow: fetch → inspect → tokenize → (audio or end)
        self.graph.set_entry_point("fetch")
        self.graph.add_edge("fetch", "inspect")
        self.graph.add_edge("inspect", "tokenize")

        # token 문제 있으면 END, 아니면 오디오 분석
        def token_cond(state: CleanerState):
            return "audio_extract" if len(state.issues) == 0 else END

        self.graph.add_conditional_edges("tokenize", token_cond)
        self.graph.add_edge("audio_extract", END)

        self.pipeline = self.graph.compile()


    # --------------------------------------------------------
    # 1) RawFetcher
    # --------------------------------------------------------
    def node_fetch(self, state: CleanerState):
        try:
            result = self.fetcher.fetch(db=state.db, conv_id=state.conv_id)

            # state 업데이트
            state.df = result["df"]
            state.speaker_segments = result["speaker_segments"]
            state.speaker_mapping = result["speaker_mapping"]
            state.audio_url = result["audio_url"]

            state.user_self_id = result["user_self_id"]
            state.user_gender = result["user_gender"]
            state.user_age = result["user_age"]
            state.user_name = result["user_name"]

            return state

        except Exception as e:
            return self.exception_handler.handle(state, e)


    # --------------------------------------------------------
    # 2) DataInspector
    # --------------------------------------------------------
    def node_inspect(self, state: CleanerState):
        try:
            df, issues = self.inspector.inspect(state.df, state)
            state.inspected_df = df
            state.issues.extend(issues)
            return state

        except Exception as e:
            return self.exception_handler.handle(state, e)


    # --------------------------------------------------------
    # 3) TokenCounter
    # --------------------------------------------------------
    def node_tokenize(self, state: CleanerState):
        try:
            df, issues = self.token_counter.count(state.inspected_df, state)
            state.issues.extend(issues)
            return state

        except Exception as e:
            return self.exception_handler.handle(state, e)


    # --------------------------------------------------------
    # 4) AudioFeatureExtractor
    # --------------------------------------------------------
    def node_audio_extract(self, state: CleanerState):
        try:
            updated = self.audio_extractor.extract(
                audio_url=state.audio_url,
                speaker_segments=state.speaker_segments
            )
            state.audio_segments_with_features = updated
            return state

        except Exception as e:
            return self.exception_handler.handle(state, e)


    # --------------------------------------------------------
    # ⭐ 실행 부분 (AnalysisGraph 입력 완전체 반환)
    # --------------------------------------------------------
    def run(self, db: Session, conv_id: str) -> Dict[str, Any]:

        state = CleanerState(
            db=db,
            conv_id=conv_id,
            verbose=self.verbose,
        )

        # 👉 LangGraph 구버전은 dict로 반환함
        final_state = self.pipeline.invoke(state)   # <--- dict임

        # 1) speaker_mapping 확인
        speaker_mapping = final_state.get("speaker_mapping")
        if not speaker_mapping:
            raise ValueError("❌ speaker_mapping 없음 — Cleaner 실패")

        # 2) user speaker label
        user_ids = speaker_mapping.get("user_ids", {})
        if len(user_ids) == 0:
            raise ValueError("❌ user_ids 없음")

        user_speaker_label = list(user_ids.keys())[0]

        # 3) 상대방
        other_speaker_label = (
            "SPEAKER_0B" if user_speaker_label == "SPEAKER_0A" else "SPEAKER_0A"
        )
        speaker_names = speaker_mapping.get("speaker_names", {})
        other_display_name = speaker_names.get(other_speaker_label, "상대방")

        # 4) 반환 (AnalysisGraph 입력 그대로)
        return {
            "speaker_segments": final_state.get("audio_segments_with_features"),
            "speaker_mapping": speaker_mapping,
            "user_id": final_state.get("user_self_id"),
            "user_name": final_state.get("user_name"),
            "user_gender": final_state.get("user_gender"),
            "user_age": final_state.get("user_age"),
            "user_speaker_label": user_speaker_label,
            "other_speaker_label": other_speaker_label,
            "other_display_name": other_display_name,
            "issues": final_state.get("issues", []),
        }
