# app/agent/QA/nodes.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
from app.core.config import settings
from langchain_openai import ChatOpenAI
import pandas as pd

# =====================================
# ✅ Mock DB 테이블 (ERD 기반)
# =====================================
analysis_result_df = pd.DataFrame([
    {
        "analysis_id": 1,
        "user_id": "201",
        "conv_id": "C001",
        "summary": "따뜻한 가족 간 대화",
        "style_analysis": {"emotion": "긍정적", "tone": "편안함"},
        "score": 0.82,
    }
])

# =====================================
# ✅ ScoreEvaluator (LLM 기반 신뢰도 평가)
# =====================================
@dataclass
class ScoreEvaluator:
    verbose: bool = False

    def evaluate(self, analysis_result: Dict[str, Any]) -> float:
        """
        감정, 톤, 요약 내용 등을 기반으로 신뢰도를 평가하는 LLM Agent.
        """
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)
        prompt = f"""
        다음 분석 결과의 신뢰도를 0~1 사이 실수로 평가해줘.
        - 0.8 이상: 매우 신뢰할 수 있음
        - 0.65~0.8: 보통 수준
        - 0.65 미만: 재분석 필요
        분석 결과:
        {analysis_result}
        """
        try:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            # 단순히 LLM 결과에 수치 포함되어 있다 가정 (mock fallback)
            score = float(analysis_result.get("score", 0.8))
            if self.verbose:
                print(f"🤖 [LLM 평가 응답] {content}")
            return min(max(score, 0), 1.0)
        except Exception as e:
            print(f"⚠️ 신뢰도 평가 실패: {e}")
            return 0.0

# =====================================
# ✅ ReAnalyzer (LLM 재분석 수행)
# =====================================
@dataclass
class ReAnalyzer:
    verbose: bool = False

    def reanalyze(self, conversation_df: pd.DataFrame, prev_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        이전 분석의 결과를 참고해 대화를 다시 분석하여 통합 결과 반환.
        """
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)
        text = "\n".join(conversation_df["text"].tolist())
        prompt = f"""
        아래 대화 내용을 다시 분석해줘. 
        이전 분석 결과는 참고용이야. 결과를 JSON 형식으로 반환해줘.
        - emotion, tone, style, score 포함
        대화 내용:
        {text}

        이전 분석 결과:
        {prev_result}
        """
        try:
            response = llm.invoke(prompt)
            if self.verbose:
                print(f"🧠 [ReAnalyzer LLM 응답] {response.content if hasattr(response, 'content') else response}")
            # mock response
            return {
                "summary": prev_result.get("summary", "대화 재분석 결과"),
                "style_analysis": {"emotion": "긍정적", "tone": "차분함"},
                "score": 0.78,
            }
        except Exception as e:
            print(f"⚠️ 재분석 실패: {e}")
            return prev_result

# =====================================
# ✅ AnalysisSaver (최종 결과 저장)
# =====================================
@dataclass
# app/agent/QA/nodes.py
@dataclass
class AnalysisSaver:
    def save_final(self, result: Dict[str, Any], state=None) -> Dict[str, Any]:
        """
        최종 QA 결과를 DB(또는 Mock DataFrame)에 반영.
        """
        global analysis_result_df
        existing = analysis_result_df[analysis_result_df["conv_id"] == state.conv_id]
        style_data = result.get("style_analysis")

        # 🧩 dict 타입은 JSON 문자열로 변환 (pandas 셀 호환)
        if isinstance(style_data, (dict, list)):
            import json
            style_data = json.dumps(style_data, ensure_ascii=False)

        if not existing.empty:
            idx = existing.index[0]
            analysis_result_df.loc[idx, "style_analysis"] = style_data
            analysis_result_df.loc[idx, "score"] = result.get("score")
        else:
            new_row = {
                "analysis_id": len(analysis_result_df) + 1,
                "user_id": state.user_id,
                "conv_id": state.conv_id,
                "summary": result.get("summary"),
                "style_analysis": style_data,
                "score": result.get("score"),
            }
            analysis_result_df = pd.concat(
                [analysis_result_df, pd.DataFrame([new_row])], ignore_index=True
            )

        # ✅ 최종 결과를 state.meta에 저장
        state.meta["final_result_df"] = analysis_result_df
        return {"status": "final_saved", "rows": len(analysis_result_df)}

