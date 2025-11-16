# backend/app/llm/agent/Feedback/graph_feedback.py
# -*- coding: utf-8 -*-

# app/agent/Feedback/graph_feedback.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

import pandas as pd
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END

from .nodes import SummaryLoaderNode, SummaryToBookQueryNode, RAGAndAdviceNode


@dataclass
class FeedbackState:
    # 공통
    db: Optional[Session] = None
    conv_id: Optional[str] = None
    id: Optional[int] = None
    conversation_df: Optional[pd.DataFrame] = None

    # Summary 로딩 후
    analysis_row: Dict[str, Any] = field(default_factory=dict)
    analysis_id: Optional[str] = None
    summary: Optional[str] = None
    score: float = 0.0
    confidence_score: float = 0.0

    # 책 검색용 쿼리
    counsel_query: Optional[str] = None
    talk_query: Optional[str] = None

    # RAG 이후
    advice_text: Optional[str] = None
    counsel_sections: List[Dict[str, Any]] = field(default_factory=list)
    talk_sections: List[Dict[str, Any]] = field(default_factory=list)

    # DB 저장 결과
    save_result: Optional[Dict[str, Any]] = None

    verbose: bool = True


class FeedbackGraph:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.loader = SummaryLoaderNode(verbose=verbose)
        self.query_maker = SummaryToBookQueryNode(verbose=verbose)
        self.rag_and_advice = RAGAndAdviceNode(verbose=verbose)

        graph = StateGraph(FeedbackState)

        graph.add_node("load_summary", self.node_load_summary)
        graph.add_node("summary_to_book_query", self.node_summary_to_book_query)
        graph.add_node("rag_and_advice", self.node_rag_and_advice)

        graph.set_entry_point("load_summary")
        graph.add_edge("load_summary", "summary_to_book_query")
        graph.add_edge("summary_to_book_query", "rag_and_advice")
        graph.add_edge("rag_and_advice", END)

        self.pipeline = graph.compile()

    def node_load_summary(self, state: FeedbackState) -> FeedbackState:
        return self.loader(state)

    def node_summary_to_book_query(self, state: FeedbackState) -> FeedbackState:
        return self.query_maker(state)

    def node_rag_and_advice(self, state: FeedbackState) -> FeedbackState:
        return self.rag_and_advice(state)

    def run(
        self,
        db: Session,
        conv_id: str,
        id: int,
        conversation_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        state = FeedbackState(
            db=db,
            conv_id=conv_id,
            id=id,
            conversation_df=conversation_df,
            verbose=self.verbose,
        )

        result_state = self.pipeline.invoke(state)

        # ✅ LangGraph가 dict를 돌려줄 수도 있고, dataclass 인스턴스를 돌려줄 수도 있으니 둘 다 처리
        if isinstance(result_state, dict):
            get = result_state.get
            conv_id_val = get("conv_id")
            id_val = get("id")
            analysis_id_val = get("analysis_id")
            summary_val = get("summary")
            advice_text_val = get("advice_text")
            save_result_val = get("save_result")
            counsel_sections_val = get("counsel_sections", [])
            talk_sections_val = get("talk_sections", [])
        else:
            # dataclass FeedbackState인 경우
            conv_id_val = result_state.conv_id
            id_val = result_state.id
            analysis_id_val = result_state.analysis_id
            summary_val = result_state.summary
            advice_text_val = result_state.advice_text
            save_result_val = result_state.save_result
            counsel_sections_val = result_state.counsel_sections
            talk_sections_val = result_state.talk_sections

        return {
            "conv_id": conv_id_val,
            "id": id_val,
            "analysis_id": analysis_id_val,
            "summary": summary_val,
            "advice_text": advice_text_val,
            "save_result": save_result_val,
            "counsel_sections": counsel_sections_val,
            "talk_sections": talk_sections_val,
        }
