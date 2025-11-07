# app/agent/QA/nodes.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
from app.core.config import settings
from langchain_openai import ChatOpenAI
import pandas as pd
from sqlalchemy.orm import Session

# =========================================
# 🔧 수정: CRUD 함수 import 추가
# =========================================
# 이유: AnalysisSaver가 DB UPDATE 수행 필요
# =========================================
from app.agent.crud import update_analysis_result


# =====================================
# ✅ ScoreEvaluator (LLM 기반 신뢰도 평가)
# =====================================
@dataclass
class ScoreEvaluator:
    """
    신뢰도 평가 (LLM 기반)
    
    변경 없음: DB 연동 불필요
    """
    verbose: bool = False

    def evaluate(self, analysis_result: Dict[str, Any]) -> tuple[float, str]:
        """
        감정, 톤, 요약 내용 등을 기반으로 신뢰도를 평가하고 근거(reason)를 함께 반환.
        """
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)
        
        # =========================================
        # 🔧 수정: 프롬프트 개선
        # =========================================
        # 이유: score를 "말하기 점수"로 명확히 설명
        # =========================================
        
        prompt = f"""
    다음은 대화 분석 결과입니다.
    이 분석 결과의 **신뢰도**를 0~1 사이 실수로 평가하고, 그 이유를 간단히 설명해주세요.

    **중요 안내:**
    - "score"는 분석 의뢰 사용자의 **말하기 능력 점수**입니다 (신뢰도가 아님)
    - "style_analysis"는 각 화자별 대화 스타일 분석 결과입니다
    - "summary"는 전체 대화 요약입니다

    **평가 기준:**
    1. style_analysis의 각 항목(말투, 성향, 관심사)이 구체적이고 일관성 있는가?
    2. summary가 대화 내용을 정확하게 요약하고 있는가?
    3. 분석 내용이 충분히 상세하고 근거가 명확한가?

    결과는 JSON으로 아래 형식으로 반환해주세요:
    {{
        "confidence": float (0~1 사이, 소수점 2자리),
        "reason": "신뢰도 평가 근거 (200자 이내)"
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
    """
    재분석 수행 (LLM 기반)
    
    변경 없음: DB 연동 불필요
    """
    verbose: bool = False

    def reanalyze(self, conversation_df: pd.DataFrame, prev_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        이전 분석의 결과를 참고해 대화를 다시 분석하여 통합 결과와 근거를 반환.
        
        Args:
            conversation_df: 대화 DataFrame
            prev_result: Analysis 단계 결과
        
        Returns:
            재분석 결과 (summary, style_analysis, score, reason 포함)
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
                    prev_result.get("style_analysis", {"emotion": "긍정적", "tone": "차분함"})
                ),
                "score": parsed.get("score", 0.75),
                "reason": parsed.get("reason", "재분석 결과에 대한 근거 없음"),
            }

            if self.verbose:
                print(f"🧠 [ReAnalyzer LLM 응답] {content[:200]}...")
                print(f"💬 [재분석 근거] {result['reason']}")

            return result

        except Exception as e:
            print(f"⚠️ 재분석 실패: {e}")
            return prev_result


# =====================================
# ✅ AnalysisSaver (DB 연동 - UPDATE)
# =====================================
@dataclass
class AnalysisSaver:
    """
    최종 결과 DB 저장 (UPDATE)
    
    🔧 수정 사항:
    - 기존: Mock DataFrame 사용
    - 변경: crud.py의 update_analysis_result() 사용
    """
    
    def save_final(self, db: Session, result: Dict[str, Any], state) -> Dict[str, Any]:
        """
        ✅ QA 최종 결과를 DB에 UPDATE
        
        🔧 수정 사항:
        - Mock DataFrame 제거
        - crud.update_analysis_result() 사용
        
        Args:
            db: SQLAlchemy 세션
            result: QA 최종 결과 (재분석 결과 또는 원본 결과)
            state: QAState
        
        Returns:
            저장 결과 dict
        
        동작:
            1. conv_id로 기존 analysis_result 조회
            2. summary, style_analysis, score, confidence_score 업데이트
            3. feedback에 재분석 근거(reason) 저장
        """
        if not db:
            raise ValueError("❌ AnalysisSaver: db 세션이 필요합니다!")
        
        if not state.conv_id:
            raise ValueError("❌ AnalysisSaver: conv_id가 필요합니다!")
        
        # =========================================
        # 🔧 수정: Mock DataFrame 제거
        # =========================================
        # 이유: 실제 DB UPDATE로 변경
        # =========================================
        
        try:
            # ✅ 업데이트할 데이터 준비
            summary = result.get("summary")
            style_analysis = result.get("style_analysis")
            score = result.get("score")
            
            # ✅ confidence_score 계산
            # QA에서 평가한 신뢰도를 confidence_score로 저장
            confidence_score = state.confidence if state.confidence else 0.0
            
            # ✅ feedback 생성
            # 재분석 사유(reason)를 feedback에 저장
            feedback_parts = []
            
            if state.reason:
                feedback_parts.append(f"[평가 근거] {state.reason}")
            
            if "reason" in result:
                feedback_parts.append(f"[재분석 근거] {result['reason']}")
            
            feedback = " | ".join(feedback_parts) if feedback_parts else None
            
            # =========================================
            # ✅ DB UPDATE 실행
            # =========================================
            # crud.update_analysis_result() 호출
            # =========================================
            
            updated = update_analysis_result(
                db=db,
                conv_id=state.conv_id,
                summary=summary,
                style_analysis=style_analysis,
                score=score,
                confidence_score=confidence_score,
                feedback=feedback,
            )
            
            if updated:
                print(f"   ✅ [AnalysisSaver] DB 업데이트 완료: analysis_id={updated['analysis_id']}")
                print(f"      → summary: {updated['summary'][:50]}...")
                print(f"      → score: {updated['score']:.2f}")
                print(f"      → confidence_score: {updated['confidence_score']:.2f}")
                
                # ✅ state.meta에 결과 저장
                state.meta["analysis_id"] = updated["analysis_id"]
                state.meta["updated"] = True
                
                return {
                    "status": "updated",
                    "analysis_id": updated["analysis_id"],
                    "score": updated["score"],
                    "confidence_score": updated["confidence_score"],
                }
            else:
                # ✅ 해당 conv_id의 분석 결과가 없는 경우
                print(f"   ⚠️ [AnalysisSaver] conv_id={state.conv_id}에 해당하는 분석 결과가 없습니다.")
                return {
                    "status": "not_found",
                    "conv_id": state.conv_id,
                }
        
        except Exception as e:
            print(f"   ❌ [AnalysisSaver] DB 업데이트 실패: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
            }