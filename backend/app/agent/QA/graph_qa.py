# app/agent/QA/graph_qa.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import pandas as pd
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from .nodes import ScoreEvaluator, ReAnalyzer, AnalysisSaver

# =====================================
# ✅ 상태 정의 (DB 세션 추가)
# =====================================
@dataclass
class QAState:
    # DB 세션 추가
    db: Optional[Session] = None
    
    # 기존 필드
    user_id: Optional[str] = None
    conv_id: Optional[Any] = None
    conversation_df: Optional[pd.DataFrame] = None
    analysis_result: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    reason: str = ""
    needs_reanalysis: bool = False 
    final_result: Optional[Dict[str, Any]] = None
    save_status: Optional[Dict[str, Any]] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    verbose: bool = True


# =====================================
# ✅ 그래프 설계 (DB 연동)
# =====================================
class QAGraph:
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.evaluator = ScoreEvaluator(verbose)
        self.reanalyzer = ReAnalyzer(verbose)
        self.saver = AnalysisSaver(verbose)  # ← 🔧 verbose 추가

        # LangGraph 구성
        self.graph = StateGraph(QAState)
        self.graph.add_node("evaluate", self.node_evaluate)
        self.graph.add_node("reanalyze", self.node_reanalyze)
        self.graph.add_node("save", self.node_save)

        self.graph.set_entry_point("evaluate")

        # 조건부 분기: 신뢰도 기준 0.65
        def confidence_condition(state: QAState):
            return "save" if state.confidence >= 0.65 else "reanalyze"

        self.graph.add_conditional_edges("evaluate", confidence_condition)
        self.graph.add_edge("reanalyze", "save")
        self.graph.add_edge("save", END)

        self.pipeline = self.graph.compile()

    # -------------------------------
    # ✅ 노드 정의
    # -------------------------------
    
    def node_evaluate(self, state: QAState):
        """
        신뢰도 평가 노드
        
        🔧 수정: evaluate() 결과를 딕셔너리로 받기
        """
        if self.verbose:
            print("\n📈 [ScoreEvaluator] 신뢰도 평가 중...")

        # =========================================
        # 🔧 수정: 딕셔너리로 받아서 각 필드에 할당
        # =========================================
        evaluation = self.evaluator.evaluate(state.analysis_result)
        
        state.confidence = evaluation["confidence"]
        state.reason = evaluation["reason"]
        state.needs_reanalysis = evaluation.get("needs_reanalysis", False)

        # ✅ 근거 출력
        print(f"   ✅ 평가 결과: {state.confidence:.2f}")
        print(f"   💬 근거(reason): {state.reason}")

        return state

    def node_reanalyze(self, state: QAState):
        """
        재분석 노드
        """
        if self.verbose:
            print("\n🔁 [ReAnalyzer] 재분석 수행 중...")

        # ✅ 이전 근거 다시 출력 (왜 재분석하는지)
        if state.reason:
            print(f"   ⚠️ 재분석 사유: {state.reason}")

        re_result = self.reanalyzer.reanalyze(state.conversation_df, state.analysis_result)
        state.final_result = re_result

        # ✅ 재분석 후 새 근거 표시
        if "reason" in re_result:
            print(f"   💬 재분석 근거(after): {re_result['reason']}")

        print("   ✅ 재분석 완료:", re_result)
        return state

    def node_save(self, state: QAState):
        """
        최종 결과 저장 노드
        
        🔧 수정 사항:
        - AnalysisSaver에 DB 세션, conv_id, confidence, reason 전달
        """
        if self.verbose:
            print("\n💾 [AnalysisSaver] 최종 결과 저장 중...")
        
        result = state.final_result or state.analysis_result
        
        # =========================================
        # 🔧 수정: save_final() 시그니처에 맞게 호출
        # =========================================
        saved = self.saver.save_final(
            db=state.db,
            conv_id=state.conv_id,
            result=result,
            confidence=state.confidence,
            reason=state.reason
            
        )
        state.save_status = saved
        print(f"   ✅ 저장 완료: {saved}")
        return state

    # -------------------------------
    # ✅ 실행 메서드 (DB 세션 주입)
    # -------------------------------
    
    def run(
        self,
        db: Session,
        conversation_df: pd.DataFrame,
        analysis_result: Dict[str, Any],
        user_id: str,
        conv_id: str
    ) -> Dict[str, Any]:
        """
        ✅ QA 파이프라인 실행 (DB 연동)
        
        Returns:
            Dict[str, Any]: QA 실행 결과 딕셔너리
        """
        if self.verbose:
            print("\n🚀 [QAGraph] 실행 시작\n" + "=" * 60)
        
        state = QAState(
            db=db,
            user_id=user_id,
            conv_id=conv_id,
            conversation_df=conversation_df,
            analysis_result=analysis_result,
            verbose=self.verbose,
        )
        
        # ✅ 파이프라인 실행
        result_state = self.pipeline.invoke(state)
        
        if self.verbose:
            print("\n✅ [QAGraph] 파이프라인 실행 완료\n" + "=" * 60)
        

        save_status = result_state.get("save_status")
        print(f"\n[DEBUG] save_status 타입: {type(save_status)}")
        print(f"[DEBUG] save_status 내용: {save_status}")
        
        # 성공 여부 판단
        success = (
            isinstance(save_status, dict) and 
            save_status.get("status") == "updated"
        )
        print(f"[DEBUG] success 계산 결과: {success}")
        print(f"[DEBUG] isinstance(save_status, dict): {isinstance(save_status, dict)}")
        if isinstance(save_status, dict):
            print(f"[DEBUG] save_status.get('status'): {save_status.get('status')}")
        
        
        return {
            "status": success,
            "conv_id": result_state.get("conv_id"),
            "user_id": result_state.get("user_id"),
            "analysis_result": result_state.get("analysis_result"),
            "confidence": result_state.get("confidence", 0.0),
            "reason": result_state.get("reason", ""),
            "needs_reanalysis": result_state.get("needs_reanalysis", False),
            "final_result": save_status,  # ← DB 저장 결과
        }