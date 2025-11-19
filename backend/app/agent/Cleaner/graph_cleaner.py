from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, List, Dict, Optional
import copy

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
import pandas as pd

from .nodes import (
    RawFetcher,
    DataInspector,
    TokenCounter,
    AudioFeatureExtractor,
    ExceptionHandler,
)


# ============================================================
# 🔥 STATE 정의
# ============================================================
@dataclass
class CleanerState:
    db: Optional[Session] = None
    conv_id: Optional[str] = None

    # Fetch 결과
    df: Optional[pd.DataFrame] = None
    speaker_segments: Optional[List[Dict]] = None
    speaker_mapping: Optional[Dict] = None
    audio_url: Optional[str] = None

    # User info
    user_self_id: Optional[int] = None
    user_gender: Optional[str] = None
    user_age: Optional[int] = None

    # Processing
    inspected_df: Optional[pd.DataFrame] = None
    audio_segments_with_features: Optional[List[Dict]] = None

    # 상태
    issues: List[str] = field(default_factory=list)
    validated: bool = False
    verbose: bool = False


# ============================================================
# 🔥 CleanerGraph (FULL DEBUG)
# ============================================================
class CleanerGraph:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose

        self.fetcher = RawFetcher()
        self.inspector = DataInspector()
        self.token_counter = TokenCounter()
        self.audio_extractor = AudioFeatureExtractor()
        self.exception_handler = ExceptionHandler()

        self.graph = StateGraph(CleanerState)

        self.graph.add_node("fetch", self.node_fetch)
        self.graph.add_node("inspect", self.node_inspect)
        self.graph.add_node("tokenize", self.node_tokenize)
        self.graph.add_node("audio_extract", self.node_audio_extract)

        self.graph.set_entry_point("fetch")
        self.graph.add_edge("fetch", "inspect")
        self.graph.add_edge("inspect", "tokenize")

        def token_cond(state: CleanerState):
            return "audio_extract" if not state.issues else END

        self.graph.add_conditional_edges("tokenize", token_cond)
        self.graph.add_edge("audio_extract", END)

        self.pipeline = self.graph.compile()


    # --------------------------------------------------------
    # 🔍 DEBUG UTIL: state snapshot
    # --------------------------------------------------------
    def debug_state(self, tag: str, state: CleanerState):
        print(f"\n--- 🔍 STATE DEBUG ({tag}) -----------------------------------")
        try:
            print(f"speaker_segments      : {type(state.speaker_segments)}, "
                  f"len={len(state.speaker_segments) if state.speaker_segments else 0}")

            print(f"audio_with_features   : {type(state.audio_segments_with_features)}, "
                  f"len={len(state.audio_segments_with_features) if state.audio_segments_with_features else 0}")

            print(f"issues                : {state.issues}")
            print(f"user_gender           : {state.user_gender}")
            print(f"user_age              : {state.user_age}")
            print(f"df shape              : {state.df.shape if state.df is not None else None}")
        except Exception as e:
            print(f"⚠️ debug_state error: {e}")
        print("-------------------------------------------------------------\n")


    # --------------------------------------------------------
    # 1) RawFetcher
    # --------------------------------------------------------
    def node_fetch(self, state: CleanerState):
        print("\n[1️⃣ RawFetcher] START")
        self.debug_state("BEFORE FETCH", state)

        try:
            result = self.fetcher.fetch(db=state.db, conv_id=state.conv_id)

            state.df = result["df"]
            state.speaker_segments = result["speaker_segments"]
            state.speaker_mapping = result["speaker_mapping"]
            state.audio_url = result["audio_url"]

            state.user_self_id = result["user_self_id"]
            state.user_gender = result["user_gender"]
            state.user_age = result["user_age"]

            print("[1️⃣ RawFetcher] SUCCESS")
            self.debug_state("AFTER FETCH", state)

            return state

        except Exception as e:
            return self.exception_handler.handle(state, e)


    # --------------------------------------------------------
    # 2) DataInspector
    # --------------------------------------------------------
    def node_inspect(self, state: CleanerState):
        print("\n[2️⃣ DataInspector] START")
        self.debug_state("BEFORE INSPECT", state)

        try:
            df, issues = self.inspector.inspect(state.df, state)
            state.inspected_df = df
            state.issues.extend(issues)

            print("[2️⃣ DataInspector] SUCCESS")
            self.debug_state("AFTER INSPECT", state)

            return state

        except Exception as e:
            return self.exception_handler.handle(state, e)


    # --------------------------------------------------------
    # 3) TokenCounter
    # --------------------------------------------------------
    def node_tokenize(self, state: CleanerState):
        print("\n[3️⃣ TokenCounter] START")
        self.debug_state("BEFORE TOKENIZE", state)

        try:
            df, issues = self.token_counter.count(state.inspected_df, state)
            state.issues.extend(issues)

            print("[3️⃣ TokenCounter] SUCCESS")
            self.debug_state("AFTER TOKENIZE", state)

            return state

        except Exception as e:
            return self.exception_handler.handle(state, e)


    # --------------------------------------------------------
    # 4) AudioFeatureExtractor
    # --------------------------------------------------------
    def node_audio_extract(self, state: CleanerState):
        print("\n[4️⃣ AudioFeatureExtractor] START")
        self.debug_state("BEFORE AUDIO EXTRACT", state)

        try:
            updated = self.audio_extractor.extract(
                audio_url=state.audio_url,
                speaker_segments=state.speaker_segments
            )
            state.audio_segments_with_features = updated

            print("[4️⃣ AudioFeatureExtractor] SUCCESS")
            self.debug_state("AFTER AUDIO EXTRACT", state)

            return state

        except Exception as e:
            return self.exception_handler.handle(state, e)


    # --------------------------------------------------------
    # 실행
    # --------------------------------------------------------
    def run(self, db: Session, conv_id: str):
        print("\n🚀 [CleanerGraph] 실행 시작\n" + "=" * 60)

        state = CleanerState(db=db, conv_id=conv_id, verbose=self.verbose)

        final_state = self.pipeline.invoke(state)

        print("\n🏁 [CleanerGraph] DONE")
        self.debug_state("FINAL STATE", final_state)

        print("=" * 60)

        # 최종 state 출력
        self.debug_state("FINAL STATE", state)

        return {
            "speaker_segments": final_state.get("audio_segments_with_features"),
            "speaker_mapping": final_state.get("speaker_mapping"),
            "user_gender": final_state.get("user_gender"),
            "user_age": final_state.get("user_age"),
            "issues": final_state.get("issues", []),
        }
