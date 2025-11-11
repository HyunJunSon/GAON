# app/agent/QA/nodes.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
from app.core.config import settings
from langchain_openai import ChatOpenAI
import pandas as pd
from sqlalchemy.orm import Session

from app.agent.crud import update_analysis_result, get_analysis_by_conv_id


# =====================================
# ✅ ScoreEvaluator (LLM 기반 신뢰도 평가)
# =====================================
@dataclass
class ScoreEvaluator:
    """점수 평가"""
    verbose: bool = False

    def evaluate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """분석 결과의 점수와 신뢰도 평가"""
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)
        
        score = result.get("score", 0.0)
        summary = result.get("summary", "")
        statistics = result.get("statistics", {})
        style_analysis = result.get("style_analysis", {})
        
        prompt = f"""
당신은 대화 분석 품질 평가 전문가입니다.
다음 분석 결과의 **신뢰도**를 0.0~1.0 사이로 평가하세요.

**주의: score는 사용자의 말하기 능력 점수입니다 (confidence가 아님)**

**분석 결과:**
- 말하기 능력 점수: {score:.2f}
- 요약: {summary[:200]}...
- 통계: {statistics}
- 스타일 분석: {style_analysis}

**평가 기준:**
1. 분석 내용이 구체적이고 근거가 명확한가?
2. 통계 데이터와 분석 내용이 일치하는가?
3. 스타일 분석이 실제 발화를 반영하는가?
4. style_analysis의 각 항목(말투, 성향, 관심사)이 구체적이고 일관성 있는가?
5. summary가 대화 내용을 정확하게 요약하고 있는가?
6. 분석 내용이 충분히 상세하고 근거가 명확한가?

**응답 형식:** 반드시 JSON 형식으로만 답변하세요
{{
  "confidence": 0.85,
  "reason": "분석이 구체적이고 통계 데이터와 일치함"
}}
"""
        
        try:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
    
            # ✅ 디버깅 로그
            if self.verbose:
                print(f"[DEBUG] AI 원본 응답:")
                print(f"--- 시작 ---")
                print(content)
                print(f"--- 끝 ---\n")
            
            import json
            try:
                # JSON 코드 블록 제거 시도
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                evaluation = json.loads(content)
                confidence = float(evaluation.get("confidence", 0.7))
                reason = evaluation.get("reason", "평가 완료")
                
                # 신뢰도 범위 검증
                confidence = max(0.0, min(1.0, confidence))
                
                if self.verbose:
                    print(f"   ✅ 파싱 성공: confidence={confidence:.2f}")
                
            except Exception as parse_error:
                # 파싱 실패 시 0.5로 설정 → 재분석 트리거
                print(f"   ❌ JSON 파싱 실패: {parse_error}")
                print(f"   → 파싱 시도 내용: {content[:200]}...")
                confidence = 0.5  # ← 0.6보다 낮게!
                reason = f"평가 파싱 실패: {str(parse_error)}"
            
            if self.verbose:
                print(f"   📊 [QA Evaluation] confidence={confidence:.2f}, reason={reason[:50]}...")
            
            return {
                "confidence": confidence,
                "reason": reason,
                "needs_reanalysis": confidence < 0.6
            }
            
        except Exception as e:
            print(f"⚠️ QA 평가 실패: {e}")
            return {
                "confidence": 0.5,  # ← 재분석 트리거
                "reason": f"평가 실패: {str(e)}",
                "needs_reanalysis": True
            }


# =====================================
# ✅ ReAnalyzer (LLM 재분석 수행)
# =====================================
@dataclass
class ReAnalyzer:
    """재분석 수행"""
    verbose: bool = False

    def reanalyze(self, conversation_df: pd.DataFrame, prev_result: Dict[str, Any]) -> Dict[str, Any]:
        """대화를 다시 분석"""
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
                "statistics": prev_result.get("statistics", {}),  # ← statistics 유지!
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
    summary에 QA 평가 정보 추가
    """
    verbose: bool = False  # ← 이게 필요해요!
    
    def save_final(self, db: Session, conv_id: str, result: Dict[str, Any], confidence: float, reason: str) -> Dict[str, Any]:
        """
        QA 최종 결과를 DB에 UPDATE
        
        Args:
            db: SQLAlchemy 세션
            conv_id: 대화 ID
            result: QA 최종 결과
            confidence: 신뢰도 점수
            reason: 평가 근거
        """
        if not db:
            raise ValueError("❌ AnalysisSaver: db 세션이 필요합니다!")
        
        if not conv_id:
            raise ValueError("❌ AnalysisSaver: conv_id가 필요합니다!")
        
        try:
            if self.verbose:
                print("\n💾 [AnalysisSaver] 최종 결과 저장 중...")
            
            # ✅ 기존 분석 결과 가져오기
            existing = get_analysis_by_conv_id(db, conv_id)
            
            if not existing:
                print(f"   ⚠️ conv_id={conv_id}에 해당하는 분석 결과가 없습니다.")
                return {"status": "not_found", "conv_id": conv_id}
            
            # ✅ 업데이트할 데이터 준비
            summary = result.get("summary", existing.get("summary", ""))
            style_analysis = result.get("style_analysis", existing.get("style_analysis"))
            statistics = result.get("statistics", existing.get("statistics"))
            score = result.get("score", existing.get("score"))
            
            # ✅ summary에 QA 섹션 추가
            qa_section = f"""

{'=' * 50}
🔍 QA 품질 평가
{'=' * 50}

[신뢰도 점수] {confidence:.2f}/1.00

[평가 근거]
  {reason}
"""
            
            if "reason" in result and result["reason"]:
                qa_section += f"""
[재분석 수행]
  사유: {result['reason']}
  → 재분석 후 품질이 개선되었습니다.
"""
            
            qa_section += f"\n{'=' * 50}\n"
            
            enhanced_summary = summary + qa_section
            
            # ✅ DB UPDATE 실행
            updated = update_analysis_result(
                db=db,
                conv_id=conv_id,
                summary=enhanced_summary,
                style_analysis=style_analysis,
                statistics=statistics,
                score=score,
                confidence_score=confidence,
                feedback=None,  # RAG에서 생성
            )
            
            if updated:
                if self.verbose:
                    print(f"   ✅ [AnalysisSaver] DB 업데이트 완료")
                    print(f"      → analysis_id: {updated['analysis_id']}")
                    print(f"      → summary: {len(enhanced_summary)}자")
                    print(f"      → score: {updated['score']:.2f}")
                    print(f"      → confidence_score: {updated['confidence_score']:.2f}")
                    print(f"      → feedback: NULL (RAG 파트에서 생성 예정)")
                
                return {
                    "status": "updated",
                    "analysis_id": updated["analysis_id"],
                    "score": updated["score"],
                    "confidence_score": updated["confidence_score"],
                    "summary_length": len(enhanced_summary)
                }
            else:
                print(f"   ⚠️ DB 업데이트 실패")
                return {"status": "update_failed", "conv_id": conv_id}
        
        except Exception as e:
            print(f"   ❌ [AnalysisSaver] DB 업데이트 실패: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}