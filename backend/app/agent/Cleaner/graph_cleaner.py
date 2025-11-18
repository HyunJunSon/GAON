from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
import pandas as pd

# 노드 import
from .nodes import (
    RawFetcher,             # raw_content + file metadata fetch
    DataInspector,          # turn ≥ 3
    TokenCounter,           # speaker별 25 tokens
    FileTypeClassifier,     # audio/text 판단
    AudioFeatureExtractor,  # 음성 요소 추출
    ContentValidator,       # 텍스트 유효성 검사
    ContentMerger,          # 텍스트 + 음성 요소 병합
    ExceptionHandler
)


# =========================================
# STATE 정의 (audio + text 병합 정보 포함)
# =========================================
@dataclass
class CleanerState:
    db: Optional[Session] = None
    conv_id: Optional[str] = None

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

    # 결과 및 검증 관련
    validated: bool = False
    issues: List[str] = field(default_factory=list)

    verbose: bool = False



# =========================================
# CLEANER GRAPH
# =========================================
class CleanerGraph:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose

        # 노드 준비
        self.fetcher = RawFetcher()
        self.inspector = DataInspector()
        self.token_counter = TokenCounter()
        self.classifier = FileTypeClassifier()
        self.validator = ContentValidator()
        self.audio_extractor = AudioFeatureExtractor()
        self.merger = ContentMerger()
        self.exception_handler = ExceptionHandler()

        # 그래프 구성
        self.graph = StateGraph(CleanerState)

        self.graph.add_node("fetch", self.node_fetch)
        self.graph.add_node("inspect", self.node_inspect)
        self.graph.add_node("tokenize", self.node_tokenize)
        self.graph.add_node("classify", self.node_classify)
        self.graph.add_node("text_validate", self.node_text_validate)
        self.graph.add_node("audio_extract", self.node_audio_extract)
        self.graph.add_node("merge", self.node_merge)

        # 시작점
        self.graph.set_entry_point("fetch")

        # 흐름 정의
        self.graph.add_edge("fetch", "inspect")
        self.graph.add_edge("inspect", "tokenize")

        # turn/token 검사 통과 후 파일 타입 분기
        def token_cond(state: CleanerState):
            return "classify" if not state.issues else END

        self.graph.add_conditional_edges("tokenize", token_cond)

        # text/audio classifier → 두 개 분기
        def classify_cond(state: CleanerState):
            if state.file_type == "text":
                return "text_validate"
            elif state.file_type == "audio":
                return "audio_extract"
            else:
                state.issues.append("unsupported_file_type")
                return END

        self.graph.add_conditional_edges("classify", classify_cond)

        # text flow
        self.graph.add_edge("text_validate", "merge")

        # audio flow
        self.graph.add_edge("audio_extract", "merge")

        # 마지막
        self.graph.add_edge("merge", END)

        # 컴파일
        self.pipeline = self.graph.compile()



    # =========================================
    # 1️⃣ RawFetcher
    # =========================================
    def node_fetch(self, state: CleanerState):
        if self.verbose:
            print("\n[1️⃣ RawFetcher] conversation_file.raw_content 불러오는 중…")

        try:
            fetch_result = self.fetcher.fetch(db=state.db, conv_id=state.conv_id)

            state.raw_df = fetch_result["df"]
            state.file_type = fetch_result["file_type"]
            state.audio_url = fetch_result["audio_url"]
            state.speaker_segments = fetch_result["speaker_segments"]

            print(f"   → file_type={state.file_type}, 발화 {len(state.raw_df)}개")

            return state

        except Exception as e:
            return self.exception_handler.handle(state, e)




    # =========================================
    # 2️⃣ DataInspector
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
    # 3️⃣ TokenCounter
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
    # 4️⃣ FileTypeClassifier
    # =========================================
    def node_classify(self, state: CleanerState):
        if self.verbose:
            print("\n[4️⃣ FileTypeClassifier] 파일 타입 분류 중…")

        try:
            file_type = self.classifier.classify(state.file_type)
            state.file_type = file_type
            print(f"   → file_type={file_type}")

            return state

        except Exception as e:
            return self.exception_handler.handle(state, e)




    # =========================================
    # 5️⃣ Text Flow: ContentValidator
    # =========================================
    def node_text_validate(self, state: CleanerState):
        if self.verbose:
            print("\n[5️⃣ ContentValidator] 텍스트 검증 중…")

        try:
            validated_df = self.validator.validate(state.inspected_df)
            state.validated_df = validated_df
            return state

        except Exception as e:
            return self.exception_handler.handle(state, e)




    # =========================================
    # 6️⃣ Audio Flow: AudioFeatureExtractor
    # =========================================
    def node_audio_extract(self, state: CleanerState):
        if self.verbose:
            print("\n[6️⃣ AudioFeatureExtractor] 음성 분석 중…")

        try:
            features = self.audio_extractor.extract(
                audio_url=state.audio_url,
                speaker_segments=state.speaker_segments
            )
            state.audio_features = features
            return state

        except Exception as e:
            return self.exception_handler.handle(state, e)




    # =========================================
    # 7️⃣ ContentMerger
    # =========================================
    def node_merge(self, state: CleanerState):
        if self.verbose:
            print("\n[7️⃣ ContentMerger] 텍스트 + 음성 요소 병합 중…")

        try:
            merged_df = self.merger.merge(
                text_df=state.inspected_df,
                audio_features=state.audio_features
            )
            state.merged_df = merged_df
            state.validated = True
            return state

        except Exception as e:
            return self.exception_handler.handle(state, e)




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
            print("🏁 [CleanerGraph] 완료\n" + "=" * 60)

        return final_state
