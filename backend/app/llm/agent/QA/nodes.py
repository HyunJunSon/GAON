# app/agent/QA/nodes.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
from app.core.config import settings
from langchain_openai import ChatOpenAI
import pandas as pd
from sqlalchemy.orm import Session
import logging

from app.llm.agent.crud import update_analysis_result, get_analysis_by_conv_id
from app.llm.cloud_functions.rag_trigger.rag.vector_db.vector_db_manager import VectorDBManager, EmbeddingService

logger = logging.getLogger(__name__)


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


# =====================================
# ✅ RAG 기반 피드백 생성기
# =====================================
@dataclass
class RAGFeedbackGenerator:
    """RAG를 활용한 피드백 생성"""
    verbose: bool = False

    def generate_feedback(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """분석 결과를 바탕으로 RAG 검색 후 피드백 생성"""
        try:
            if self.verbose:
                print(f"   🤖 [RAGFeedbackGenerator] 피드백 생성 시작")
            
            # RAG 시스템 초기화
            vector_db_manager = VectorDBManager()
            embedding_service = EmbeddingService(vector_db_manager)
            
            # 분석 결과에서 핵심 키워드 추출
            summary = analysis_result.get("summary", "")
            statistics = analysis_result.get("statistics", {})
            
            # 검색 쿼리 생성 (대화의 핵심 문제점과 개선 필요 영역)
            search_query = f"""
            가족 대화 분석:
            {summary}
            
            주요 이슈:
            - 감정 표현: {statistics.get('emotion_distribution', {})}
            - 대화 패턴: 총 {statistics.get('total_utterances', 0)}회 발화
            - 소통 스타일 개선 필요
            """
            
            # RAG에서 관련 책 조언 검색
            book_advice = []
            try:
                # 쿼리 임베딩 생성
                query_embedding = embedding_service.create_embedding(search_query)
                
                # 관련 조언 검색 (60% 이상 유사도만)
                similar_results = vector_db_manager.find_similar(
                    query_embedding=query_embedding,
                    top_k=3,
                    threshold=0.6  # 60% 이상 유사도
                )
                
                book_advice = [
                    {
                        "advice": content,
                        "similarity": similarity,
                        "source_id": str(advice_id)
                    }
                    for content, similarity, advice_id in similar_results
                    if similarity >= 0.6  # 60% 이상만 포함
                ]
                
                if self.verbose:
                    print(f"      → RAG 검색 완료: {len(book_advice)}개 관련 조언 발견")
                
            except Exception as e:
                logger.warning(f"RAG 검색 실패, 기본 피드백으로 진행: {str(e)}")
            
            # LLM을 사용한 피드백 생성
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                api_key=settings.openai_api_key
            )
            
            # 시스템 프롬프트 (책 조언 포함)
            system_prompt = """
당신은 가족 대화 분석 전문가입니다. 
분석 결과를 바탕으로 구체적이고 실용적인 개선 피드백을 제공해주세요.

**피드백 작성 원칙:**
1. 긍정적인 부분을 먼저 언급
2. 개선이 필요한 부분을 구체적으로 지적
3. 실천 가능한 개선 방안 제시
4. 가족 관계 개선에 도움이 되는 조언

**출력 형식:**
## 잘하고 있는 점
- [구체적인 긍정적 피드백]

## 개선이 필요한 부분  
- [구체적인 개선점]

## 실천 방안
- [구체적인 실천 방법]
"""

            # 관련 책 조언이 있으면 프롬프트에 추가
            if book_advice:
                advice_text = "\n".join([
                    f"📚 조언 {i+1} (관련도: {advice['similarity']:.1%}): {advice['advice']}"
                    for i, advice in enumerate(book_advice)
                ])
                system_prompt += f"""

## 참고할 전문가 조언
다음은 이 대화 상황과 관련된 전문서적의 조언들입니다 (60% 이상 관련도):

{advice_text}

위 전문가 조언들을 참고하여 더 구체적이고 근거 있는 피드백을 제공해주세요.
조언을 직접 인용하거나 참고했다면 "전문가 조언에 따르면..." 등으로 언급해주세요.
"""

            # 사용자 메시지 구성
            user_message = f"""
다음 대화 분석 결과를 바탕으로 피드백을 작성해주세요:

**분석 요약:**
{summary}

**주요 통계:**
{statistics}

**분석 점수:** {analysis_result.get('score', 0)}/100
**신뢰도:** {analysis_result.get('confidence_score', 0)}/100
"""

            # LLM 호출
            from langchain_core.messages import HumanMessage, SystemMessage
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = llm.invoke(messages)
            feedback = response.content
            
            if self.verbose:
                print(f"      → 피드백 생성 완료 (길이: {len(feedback)}자, 조언: {len(book_advice)}개)")
            
            return {
                "status": "success",
                "feedback": feedback,
                "book_advice": book_advice,
                "rag_used": len(book_advice) > 0,
                "book_advice_count": len(book_advice)
            }
            
        except Exception as e:
            logger.error(f"RAG 피드백 생성 실패: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "feedback": None
            }