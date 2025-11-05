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

    def evaluate(self, analysis_result: Dict[str, Any]) -> tuple[float, str]:
        """
        감정, 톤, 요약 내용 등을 기반으로 신뢰도를 평가하고 근거(reason)를 함께 반환.
        """
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)
        prompt = f"""
        다음 분석 결과의 신뢰도를 0~1 사이 실수로 평가하고,
        그 이유를 간단히 설명해줘.
        결과는 JSON으로 아래 형식으로 반환해줘.
        {{
            "confidence": float,
            "reason": "string"
        }}
        분석 결과:
        {analysis_result}
        """
        try:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)

            # ✅ JSON 파싱 + fallback 로직 추가
            import json, re
            try:
                parsed = json.loads(content)
                confidence = parsed.get("confidence", 0.0)
                reason = parsed.get("reason", "No reason provided")
            except json.JSONDecodeError:
                # 🔁 fallback: 일반 텍스트에서 숫자 추출
                match = re.search(r"([0-1]\.\d+|\d\.\d+|\d)", content)
                confidence = float(match.group(1)) if match else 0.0
                reason = content.strip()[:200]  # 텍스트 일부를 reason으로 사용

            if self.verbose:
                print(f"🤖 [LLM 평가 결과] 신뢰도: {confidence:.2f}, 근거: {reason}")

            return confidence, reason

        except Exception as e:
            print(f"⚠️ LLM 평가 실패: {e}")
            return 0.0, str(e)


# =====================================
# ✅ ReAnalyzer (LLM 재분석 수행)
# =====================================
@dataclass
class ReAnalyzer:
    verbose: bool = False

    def reanalyze(self, conversation_df: pd.DataFrame, prev_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        이전 분석의 결과를 참고해 대화를 다시 분석하여 통합 결과와 근거를 반환.
        """
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)
        text = "\n".join(conversation_df["text"].tolist())
        prompt = f"""
        아래 대화 내용을 다시 분석해줘.
        이전 분석 결과는 참고용이야. 
        결과를 JSON 형식으로 반환해줘.
        {{
            "summary": "string",
            "style_analysis": {{"emotion": "string", "tone": "string"}},
            "score": float,
            "reason": "string"
        }}
        대화 내용:
        {text}

        이전 분석 결과:
        {prev_result}
        """
        try:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            import json, re

            # JSON 파싱 시도
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                parsed = {}
                match = re.search(r"([0-1]\.\d+|\d\.\d+|\d)", content)
                parsed["score"] = float(match.group(1)) if match else 0.75
                parsed["reason"] = content.strip()[:200]

            result = {
                "summary": parsed.get("summary", prev_result.get("summary", "대화 재분석 결과")),
                "style_analysis": parsed.get(
                    "style_analysis",
                    {"emotion": "긍정적", "tone": "차분함"}
                ),
                "score": parsed.get("score", 0.75),
                "reason": parsed.get("reason", "재분석 결과에 대한 근거 없음"),
            }

            if self.verbose:
                print(f"🧠 [ReAnalyzer LLM 응답] {content}")
                print(f"💬 [재분석 근거] {result['reason']}")

            return result

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

