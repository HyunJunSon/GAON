from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
import pandas as pd

# 노드 import
from .nodes import (
    RawFetcher,
    DataInspector,
    TokenCounter,
    FileTypeClassifier,
    AudioFeatureExtractor,
    ContentValidator,
    ContentMerger,
    ExceptionHandler
)

# =========================================
# STATE 정의
# =========================================
@dataclass
class CleanerState:
    db: Optional[Session] = None
    conv_id: Optional[str] = None
    conversation_df: Optional[pd.DataFrame] = None   # ⭐ NEW

    # RAW
    raw_df: Optional[pd.DataFrame] = None
    file_type: Optional[str] = None
    audio_url: Optional[str] = None
    speaker_segments: Optional[List[Dict]] = None

    # PROCESSING
    inspected_df: Optional[pd.DataFrame] = None
    validated_df: Optional[pd.DataFrame] = None
    audio_features: Optional[List[Dict]] = None
    merged_df: Optional[pd.DataFrame] = None

    # 결과
    validated: bool = False
    issues: List[str] = field(default_factory=list)

    verbose: bool = False



# =========================================
# CLEANER GRAPH
# =========================================
class CleanerGraph:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose

        # 노드
        self.fetcher = RawFetcher()
        self.inspector = DataInspector()
        self.token_counter = TokenCounter()
        self.classifier = FileTypeClassifier()
        self.audio_extractor = AudioFeatureExtractor()
        self.validator = ContentValidator()
        self.merger = ContentMerger()
        self.exception_handler = ExceptionHandler()

        # 그래프 컴포넌트
        self.graph = StateGraph(CleanerState)

        self.graph.add_node("fetch", self.node_fetch)
        self.graph.add_node("inspect", self.node_inspect)
        self.graph.add_node("tokenize", self.node_tokenize)
        self.graph.add_node("classify", self.node_classify)
        self.graph.add_node("text_validate", self.node_text_validate)
        self.graph.add_node("audio_extract", self.node_audio_extract)
        self.graph.add_node("merge", self.node_merge)

        self.graph.set_entry_point("fetch")

        # fetch → inspect → tokenize
        self.graph.add_edge("fetch", "inspect")
        self.graph.add_edge("inspect", "tokenize")

        # tokenizer pass 여부
        def token_cond(state: CleanerState):
            return "classify" if not state.issues else END

        self.graph.add_conditional_edges("tokenize", token_cond)

        # classify 분기
        def classify_cond(state: CleanerState):
            if state.file_type == "text":
                return "text_validate"
            elif state.file_type == "audio":
                return "audio_extract"
            else:
                state.issues.append("unsupported_file_type")
                return END

        self.graph.add_conditional_edges("classify", classify_cond)

        self.graph.add_edge("text_validate", "merge")
        self.graph.add_edge("audio_extract", "merge")

        self.graph.add_edge("merge", END)

        self.pipeline = self.graph.compile()


    # =========================================
    # 1️⃣ RawFetcher
    # =========================================
    def node_fetch(self, state: CleanerState):
        if self.verbose:
            print("\n[1️⃣ RawFetcher] DF or raw_content 불러오는 중…")

        try:
            # ⭐ NEW — 외부 conversation_df 제공된 경우
            if state.conversation_df is not None:
                print("   → 외부 DF 사용하여 fetch 생략 (raw_content 미사용)")
                fetch_result = self.fetcher.fetch(
                    db=state.db,
                    conv_id=state.conv_id,
                    conversation_df=state.conversation_df,  # ⭐ NEW
                )

            else:
                # 기존 DB raw_content 방식
                fetch_result = self.fetcher.fetch(
                    db=state.db,
                    conv_id=state.conv_id
                )

            # 공통 저장
            state.raw_df = fetch_result["df"]
            state.file_type = fetch_result["file_type"]
            state.audio_url = fetch_result["audio_url"]
            state.speaker_segments = fetch_result["speaker_segments"]

            print(f"   → file_type={state.file_type}, 발화 {len(state.raw_df)}개")

            return state

        except Exception as e:
            return self.exception_handler.handle(state, e)


    # =========================================
    def node_inspect(self, state: CleanerState):
        if self.verbose:
            print("\n[2️⃣ DataInspector] turn 검사 중…")

        try:
            df, issues = self.inspector.inspect(state.raw_df, state)
            state.inspected_df = df
            state.issues.extend(issues)

            if issues:
                print("   ❌ turn 부족:", issues)
            else:
                print("   ✅ turn 검사 통과")
            return state
        except Exception as e:
            return self.exception_handler.handle(state, e)


    # =========================================
    def node_tokenize(self, state: CleanerState):
        if self.verbose:
            print("\n[3️⃣ TokenCounter] 화자별 25 어절 검사 중…")

        try:
            df, issues = self.token_counter.count(state.inspected_df, state)
            state.issues.extend(issues)

            if issues:
                print("   ❌ 어절 부족:", issues)
            else:
                print("   ✅ 어절 검사 통과")

            return state
        except Exception as e:
            return self.exception_handler.handle(state, e)


    # =========================================
    def node_classify(self, state: CleanerState):
        if self.verbose:
            print("\n[4️⃣ FileTypeClassifier] 파일 타입 분류 중…")

        try:
            state.file_type = self.classifier.classify(state.file_type)
            print(f"   → file_type={state.file_type}")
            return state
        except Exception as e:
            return self.exception_handler.handle(state, e)


    # =========================================
    def node_text_validate(self, state: CleanerState):
        if self.verbose:
            print("\n[5️⃣ ContentValidator] 텍스트 검증 중…")

        try:
            state.validated_df = self.validator.validate(state.inspected_df)
            return state
        except Exception as e:
            return self.exception_handler.handle(state, e)


    # =========================================
    def node_audio_extract(self, state: CleanerState):
        if self.verbose:
            print("\n[6️⃣ AudioFeatureExtractor] 음성 분석 중…")

        try:
            state.audio_features = self.audio_extractor.extract(
                audio_url=state.audio_url,
                speaker_segments=state.speaker_segments,
            )
            return state
        except Exception as e:
            return self.exception_handler.handle(state, e)


    # =========================================
    def node_merge(self, state: CleanerState):
        if self.verbose:
            print("\n[7️⃣ ContentMerger] 텍스트 + 음성 병합 중…")

        try:
            state.merged_df = self.merger.merge(
                text_df=state.inspected_df,
                audio_features=state.audio_features,
            )
            state.validated = True
            return state
        except Exception as e:
            return self.exception_handler.handle(state, e)


    # =========================================
    # 실행
    # =========================================
    def run(self, db: Session, conv_id: str, conversation_df=None):  
        if self.verbose:
            print("\n🚀 [CleanerGraph] 실행 시작\n" + "=" * 60)

        state = CleanerState(
            db=db,
            conv_id=conv_id,
            conversation_df=conversation_df,    
            verbose=self.verbose,
        )

        final_state = self.pipeline.invoke(state)

        if self.verbose:
            print("🏁 [CleanerGraph] 완료\n" + "=" * 60)

        return final_state
