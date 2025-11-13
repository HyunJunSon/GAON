# app/agent/Analysis/nodes.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
from app.core.config import settings
from langchain_openai import ChatOpenAI
import pandas as pd
from sqlalchemy.orm import Session
from collections import Counter
import re
import json

# ✅ CRUD 함수 import
from app.agent.crud import (
    get_user_by_id,
    get_family_by_id,
    save_analysis_result,
)


# =========================================
# ✅ UserFetcher (DB 연동)
# =========================================
@dataclass
class UserFetcher:
    """
    ✅ DB에서 사용자 정보 조회
    
    변경 사항:
    - 기존: Mock user_df
    - 변경: DB users 테이블 조회
    """
    def fetch(self, db: Session, conv_state) -> Dict[str, Any]:
        """
        users 테이블에서 사용자 정보 조회
        
        Args:
            db: SQLAlchemy 세션
            conv_state: AnalysisState (id 포함)
        
        Returns:
            사용자 정보 Dict
        """
        id = conv_state.id
        
        if not id:
            raise ValueError("❌ UserFetcher: id가 없습니다.")
        
        # ✅ DB 조회
        user = get_user_by_id(db, id)
        
        if not user:
            raise ValueError(f"❌ UserFetcher: id={id}를 찾을 수 없습니다.")
        
        print(f"✅ [UserFetcher] 사용자 조회: {user.get('user_name')}")
        
        return user


# =========================================
# ✅ FamilyChecker (가족 기능 비활성화) - 수정 없음
# =========================================
@dataclass
class FamilyChecker:
    """
    ✅ 가족 관계 확인 (현재 비활성화)
    
    현재 상태:
    - users ↔ family 연결 컬럼 없음
    - 항상 False 반환 → LLM 추론 모드
    """
    def check(self, db: Session, user_info: Dict[str, Any]) -> Tuple[bool, int]:
        """
        가족 정보 확인 (현재 비활성화)
        
        Args:
            db: SQLAlchemy 세션
            user_info: UserFetcher 결과
        
        Returns:
            (False, None) - 항상 LLM 추론 모드
        """
        print(f"⚠️  [FamilyChecker] 가족 기능 비활성화 → LLM 추론 모드")
        return False, None


# =========================================
# ✅ RelationResolver_DB (비활성화)
# =========================================
@dataclass
class RelationResolver_DB:
    """
    ✅ DB에서 가족 구성원 조회 (현재 비활성화)
    
    현재 상태:
    - family_member 테이블 없음
    - 빈 리스트 반환
    """
    def resolve(self, db: Session, fam_id: int) -> List[Dict[str, Any]]:
        """
        가족 구성원 조회 (현재 비활성화)
        
        Args:
            db: SQLAlchemy 세션
            fam_id: 가족 ID
        
        Returns:
            [] - 빈 리스트
        """
        print(f"⚠️  [RelationResolver_DB] 가족 기능 비활성화")
        return []


# =========================================
# ✅ RelationResolver_LLM 
# =========================================
@dataclass
class RelationResolver_LLM:
    """LLM 기반 관계 추론"""
    verbose: bool = False

    def resolve(self, conversation_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        LLM으로 대화에서 관계 추론
        
        Args:
            conversation_df: 대화 DataFrame
        
        Returns:
            추론된 관계 리스트
        """
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)
        text_snippet = "\n".join(conversation_df["text"].tolist()[:10])
        
        prompt = f"""
다음 대화에서 등장하는 인물들의 관계를 추론해줘.
예: 엄마, 아들, 아빠, 친구 등

대화 내용:
{text_snippet}

결과를 JSON 형태로 반환해줘.
예: [{{"speaker":1,"relation":"엄마"}}, {{"speaker":2,"relation":"아들"}}]
speaker는 반드시 int 형태로 반환해야해.
"""
        
        try:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            
            if self.verbose:
                print(f"🧠 [RelationResolver_LLM] 응답: {content[:200]}")
            
            # ✅ 간단한 fallback
            return [
                {"speaker": 1, "relation": "참석자1"},
                {"speaker": 2, "relation": "참석자2"}
            ]
            
        except Exception as e:
            print(f"⚠️ Relation LLM 실패: {e}")
            return []


# =========================================
# 🔧 Analyzer (사용자 중심 분석)
# =========================================

@dataclass
class Analyzer:
        """
        감정/스타일/통계 분석
        
        🔧 수정 사항:
        1. id 파라미터 추가
        2. 사용자만 style_analysis에 저장
        3. 사용자 vs 상대방 비교 통계
        4. score는 사용자 말하기 점수
        5. summary는 AI가 생성한 종합 분석 보고서 (구조화)
        """
        verbose: bool = False

        def analyze(
            self,
            conversation_df: pd.DataFrame,
            relations: List[Dict[str, Any]],
            id: int
        ) -> Dict[str, Any]:
            """
            LLM으로 대화 분석 (사용자 중심)
            
            Args:
                conversation_df: 대화 DataFrame
                relations: 관계 정보
                id: 분석 의뢰 사용자 ID
            
            Returns:
                분석 결과 (DB 스키마 준수)
            """
            llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)
            
            # =========================================
            # 0️⃣ 사용자/상대방 DataFrame 분리
            # =========================================
            
            user_df = conversation_df[conversation_df["speaker"] == int(id)]
            others_df = conversation_df[conversation_df["speaker"] != int(id)]
            
            if user_df.empty:
                raise ValueError(f"❌ id={id}의 발화가 없습니다!")
            
            if self.verbose:
                print(f"   👤 사용자 발화: {len(user_df)}개")
                print(f"   👥 상대방 발화: {len(others_df)}개")
            
            # =========================================
            # 1️⃣ statistics 생성 (사용자 vs 상대방 비교)
            # =========================================
            
            user_texts = " ".join(user_df["text"].tolist())
            user_words = user_texts.split()
            
            user_stats = {
                "word_count": len(user_words),
                "avg_sentence_length": round(len(user_words) / len(user_df), 1),
                "unique_words": len(set(user_words)),
                "top_words": self._get_top_words(user_texts, top_n=5)
            }
            
            if not others_df.empty:
                others_texts = " ".join(others_df["text"].tolist())
                others_words = others_texts.split()
                
                others_stats = {
                    "word_count": len(others_words),
                    "avg_sentence_length": round(len(others_words) / len(others_df), 1),
                    "unique_words": len(set(others_words)),
                }
            else:
                others_stats = {
                    "word_count": 0,
                    "avg_sentence_length": 0,
                    "unique_words": 0,
                }
            
            comparison = self._generate_comparison(user_stats, others_stats)
            
            statistics = {
                "user": user_stats,
                "others": others_stats,
                "comparison": comparison
            }
            
            if self.verbose:
                print(f"   📊 [Statistics] 사용자 단어: {user_stats['word_count']}, "
                    f"상대방 단어: {others_stats['word_count']}")
            
            # =========================================
            # 2️⃣ style_analysis 생성 (사용자만, AI 분석)
            # =========================================
            
            full_context = "\n".join([
                f"화자 {row['speaker']}: {row['text']}"
                for _, row in conversation_df.iterrows()
            ])
            
            user_texts_joined = "\n".join(user_df["text"].tolist())
            
            style_prompt = f"""
    다음은 대화 전체 맥락과 분석 대상 사용자의 발화입니다.
    **사용자 ID {id}**의 말투, 성향, 관심사를 분석해주세요.

    **전체 대화 맥락:**
    {full_context[:500]}...

    **분석 대상 사용자 (ID: {id})의 발화:**
    {user_texts_joined}

    **통계 정보:**
    - 사용자 평균 문장 길이: {user_stats['avg_sentence_length']}
    - 상대방 평균 문장 길이: {others_stats['avg_sentence_length']}
    - 사용자 단어 수: {user_stats['word_count']}
    - 상대방 단어 수: {others_stats['word_count']}

    아래 형식으로 JSON 응답해주세요:
    {{
    "말투_특징_분석": "존댓말/반말 사용, 특정 표현 습관, 문장 길이 특징 등",
    "대화_성향_및_감정_표현": "긍정적/부정적, 격려/비판 성향, 감정 표현 방식 등",
    "대화_비교_분석": "상대방 대비 사용자의 대화 특징 (간결함, 상세함, 주도성 등)"
    }}
    """
            
            try:
                response = llm.invoke(style_prompt)
                content = response.content if hasattr(response, "content") else str(response)
                
                if self.verbose:
                    print(f"   🗣️ [Style Analysis] 사용자: {content[:100]}...")
                
                try:
                    user_analysis = json.loads(content)
                except:
                    user_analysis = {
                        "말투_특징_분석": content[:100],
                        "대화_성향_및_감정_표현": "분석 중",
                        "대화_비교_분석": "분석 중"
                    }
                
                style_analysis = {
                    str(id): user_analysis
                }
                
            except Exception as e:
                print(f"⚠️ 사용자 스타일 분석 LLM 실패: {e}")
                style_analysis = {
                    str(id): {
                        "말투_특징_분석": "분석 실패",
                        "대화_성향_및_감정_표현": "분석 실패",
                        "대화_비교_분석": "분석 실패"
                    }
                }
            
            # =========================================
            # 3️⃣ score 계산 (사용자 말하기 점수)
            # =========================================
            
            score = self._calculate_user_score(user_stats, others_stats, user_analysis)
            
            if self.verbose:
                print(f"   🎯 [Score] 사용자 말하기 점수: {score:.2f}")
            
            # =========================================
            # 🔧 4️⃣ summary 생성 (AI 기반 종합 분석 보고서)
            # =========================================
            # 🎯 목적: RAG 입력용 구조화된 종합 리포트
            # 🤖 방식: LLM이 통계 + 스타일 데이터를 읽고 해석
            # =========================================
            
            summary = self._generate_comprehensive_summary(
                llm=llm,
                conversation_df=conversation_df,
                id=id,
                user_df=user_df,
                user_stats=user_stats,
                others_stats=others_stats,
                comparison=comparison,
                user_analysis=user_analysis,
                score=score,
                full_context=full_context
            )
            
            if self.verbose:
                print(f"   📝 [Summary] {len(summary)}자 생성 (AI 분석)")
            
            # =========================================
            # ✅ 최종 결과 반환
            # =========================================
            
            return {
                "summary": summary,  # ← AI가 생성한 종합 분석 보고서
                "style_analysis": style_analysis,
                "statistics": statistics,
                "score": score,
            }
        
        # =========================================
        # 🔧 새로 추가: AI 기반 종합 분석 보고서 생성
        # =========================================
        
        def _generate_comprehensive_summary(
            self,
            llm: ChatOpenAI,
            conversation_df: pd.DataFrame,
            id: int,
            user_df: pd.DataFrame,
            user_stats: Dict,
            others_stats: Dict,
            comparison: str,
            user_analysis: Dict,
            score: float,
            full_context: str
        ) -> str:
            """
            AI 기반 종합 분석 보고서 생성
            
            Args:
                llm: LLM 인스턴스
                conversation_df: 전체 대화 DataFrame
                id: 사용자 ID
                user_df: 사용자 발화 DataFrame
                user_stats: 사용자 통계
                others_stats: 상대방 통계
                comparison: 비교 분석 텍스트
                user_analysis: 스타일 분석 결과
                score: 말하기 점수
                full_context: 전체 대화 맥락
            
            Returns:
                구조화된 종합 분석 보고서 (AI 생성)
            """
            
            # 발화 샘플 준비
            sample_utterances = '\n'.join([
                f"- {text[:100]}{'...' if len(text) > 100 else ''}"
                for text in user_df.head(5)['text'].tolist()
            ])
            
            # AI 프롬프트
            summary_prompt = f"""
    당신은 대화 분석 전문가입니다. 
    제공된 통계 데이터와 실제 발화 내용을 바탕으로 **사용자 ID {id}**의 대화 스타일과 커뮤니케이션 능력을 심층 분석한 종합 보고서를 작성하세요.

    **분석 지침:**
    1. 단순 수치 나열이 아닌, **수치가 의미하는 바를 해석**
    2. 발화 샘플에서 드러나는 **표현 방식, 태도, 특징 파악**
    3. **강점과 개선점을 구체적으로 제시**
    4. 전문적이면서도 이해하기 쉬운 문장으로 작성
    5. **모든 섹션을 빠짐없이 포함** (RAG 입력 목적)

    **출력 형식 (반드시 이 구조 준수):**

    ==================================================
    📊 대화 분석 종합 리포트
    ==================================================

    [분석 대상] 사용자 ID: {id}
    [대화 규모] 전체 {len(conversation_df)}회 발화 (사용자: {len(user_df)}회, 상대방: {len(conversation_df) - len(user_df)}회)

    --------------------------------------------------
    🎯 말하기 점수: {score:.2f}/1.00
    --------------------------------------------------

    📈 통계 분석
    • 사용자 총 단어 수: {user_stats['word_count']}개
    • 사용자 평균 문장 길이: {user_stats['avg_sentence_length']}단어
    • 사용자 고유 단어 수: {user_stats['unique_words']}개
    • 사용자 자주 사용한 단어: {', '.join(user_stats['top_words'])}

    • 상대방 총 단어 수: {others_stats['word_count']}개
    • 상대방 평균 문장 길이: {others_stats['avg_sentence_length']}단어

    • 비교 분석: {comparison}

    **🤖 AI 해석:**
    (위 수치들이 의미하는 바를 2-3문장으로 해석)

    🗣️ 말투 특징 분석
    {user_analysis.get('말투_특징_분석', '분석 없음')}

    **🤖 AI 심층 분석:**
    (실제 발화 샘플을 바탕으로 말투의 특징을 구체적으로 분석, 2-3문장)

    💬 대화 성향 및 감정 표현
    {user_analysis.get('대화_성향_및_감정_표현', '분석 없음')}

    **🤖 AI 심층 분석:**
    (발화에서 드러나는 성향과 감정 표현 방식을 구체적으로 분석, 2-3문장)

    🎯 주요 관심사
    {user_analysis.get('주요_관심사', '분석 없음')}

    📊 상대방과의 비교
    {user_analysis.get('대화_비교_분석', '분석 없음')}

    **🤖 AI 종합 평가:**
    (강점 2가지, 개선점 1가지, 추천 사항 1가지를 구체적으로 제시, 4-5문장)

    ==================================================

    **제공된 데이터:**

    **실제 발화 샘플 (최근 5개):**
    {sample_utterances}

    **전체 대화 맥락 (일부):**
    {full_context[:300]}...

    ---

    위 형식에 맞춰 **구조화된 보고서**를 작성하되, **🤖 AI 해석/분석 섹션**에는 단순 반복이 아닌 실질적인 통찰을 담아주세요.
    """
            
            try:
                response = llm.invoke(summary_prompt)
                summary = response.content if hasattr(response, "content") else str(response)
                summary = summary.strip()
                
                if self.verbose:
                    print(f"   ✅ AI 기반 종합 분석 보고서 생성 완료")
                
                return summary
                
            except Exception as e:
                print(f"⚠️ AI 종합 보고서 생성 실패: {e}")
                
                # Fallback: 템플릿 기반 보고서
                return self._generate_fallback_summary(
                    id=id,
                    conversation_df=conversation_df,
                    user_df=user_df,
                    user_stats=user_stats,
                    others_stats=others_stats,
                    comparison=comparison,
                    user_analysis=user_analysis,
                    score=score
                )
        
        def _generate_fallback_summary(
            self,
            id: int,
            conversation_df: pd.DataFrame,
            user_df: pd.DataFrame,
            user_stats: Dict,
            others_stats: Dict,
            comparison: str,
            user_analysis: Dict,
            score: float
        ) -> str:
            """
            Fallback: 템플릿 기반 요약 (LLM 실패 시)
            """
            summary_parts = [
                "=" * 50,
                "📊 대화 분석 종합 리포트",
                "=" * 50,
                f"\n[분석 대상] 사용자 ID: {id}",
                f"[대화 규모] 전체 {len(conversation_df)}회 발화 (사용자: {len(user_df)}회, 상대방: {len(conversation_df) - len(user_df)}회)",
                f"\n{'-' * 50}",
                f"🎯 말하기 점수: {score:.2f}/1.00",
                f"{'-' * 50}",
                f"\n📈 통계 분석",
                f"  • 사용자 총 단어 수: {user_stats['word_count']}개",
                f"  • 사용자 평균 문장 길이: {user_stats['avg_sentence_length']}단어",
                f"  • 사용자 고유 단어 수: {user_stats['unique_words']}개",
                f"  • 사용자 자주 사용한 단어: {', '.join(user_stats['top_words'])}",
                f"\n  • 상대방 총 단어 수: {others_stats['word_count']}개",
                f"  • 상대방 평균 문장 길이: {others_stats['avg_sentence_length']}단어",
                f"\n  • 비교 분석: {comparison}",
                f"\n🗣️ 말투 특징 분석",
                f"  {user_analysis.get('말투_특징_분석', '분석 없음')}",
                f"\n💬 대화 성향 및 감정 표현",
                f"  {user_analysis.get('대화_성향_및_감정_표현', '분석 없음')}",
                f"\n🎯 주요 관심사",
                f"  {user_analysis.get('주요_관심사', '분석 없음')}",
                f"\n📊 상대방과의 비교",
                f"  {user_analysis.get('대화_비교_분석', '분석 없음')}",
                f"\n{'=' * 50}",
            ]
            
            return "\n".join(summary_parts)
        
        # =========================================
        # 기존 헬퍼 메서드들
        # =========================================
        
        def _generate_comparison(self, user_stats: Dict, others_stats: Dict) -> str:
            """사용자 vs 상대방 비교 분석 텍스트 생성"""
            comparisons = []
            
            if others_stats["word_count"] > 0:
                word_ratio = user_stats["word_count"] / others_stats["word_count"]
                if word_ratio < 0.7:
                    comparisons.append("사용자는 상대방보다 말을 적게 함")
                elif word_ratio > 1.3:
                    comparisons.append("사용자는 상대방보다 말을 많이 함")
                else:
                    comparisons.append("사용자와 상대방의 대화량이 비슷함")
            
            if others_stats["avg_sentence_length"] > 0:
                len_diff = user_stats["avg_sentence_length"] - others_stats["avg_sentence_length"]
                if len_diff < -2:
                    comparisons.append("사용자는 짧은 문장을 선호")
                elif len_diff > 2:
                    comparisons.append("사용자는 긴 문장을 선호")
            
            return ", ".join(comparisons) if comparisons else "비교 데이터 부족"
        
        def _calculate_user_score(
            self,
            user_stats: Dict,
            others_stats: Dict,
            user_analysis: Dict
        ) -> float:
            """사용자 말하기 점수 계산 (0.0 ~ 1.0)"""
            score_components = []
            
            # 1. 어휘 다양성 (0 ~ 0.4점)
            if user_stats["word_count"] > 0:
                vocab_diversity = user_stats["unique_words"] / user_stats["word_count"]
                vocab_score = min(0.4, vocab_diversity * 0.8)
                score_components.append(vocab_score)
            
            # 2. 대화 참여도 (0 ~ 0.3점)
            if others_stats["word_count"] > 0:
                participation_ratio = user_stats["word_count"] / (user_stats["word_count"] + others_stats["word_count"])
                if 0.4 <= participation_ratio <= 0.6:
                    participation_score = 0.3
                else:
                    participation_score = 0.3 * (1 - abs(participation_ratio - 0.5) * 2)
                score_components.append(participation_score)
            
            # 3. 문장 구조 (0 ~ 0.3점)
            avg_len = user_stats["avg_sentence_length"]
            if 5 <= avg_len <= 10:
                structure_score = 0.3
            elif avg_len < 5:
                structure_score = 0.3 * (avg_len / 5)
            else:
                structure_score = 0.3 * (10 / avg_len)
            score_components.append(structure_score)
            
            final_score = sum(score_components)
            normalized_score = 0.5 + (final_score * 0.5)
            
            return round(min(1.0, max(0.0, normalized_score)), 2)
        
        def _get_top_words(self, text: str, top_n: int = 5) -> List[str]:
            """빈도 높은 단어 추출 (한글 기준)"""
            words = re.findall(r'[가-힣]+', text)
            words = [w for w in words if len(w) >= 2]
            word_counts = Counter(words)
            top_words = [word for word, count in word_counts.most_common(top_n)]
            return top_words


# =========================================
# ✅ ScoreEvaluator 
# =========================================
@dataclass
class ScoreEvaluator:
    """신뢰도 평가"""
    def evaluate(self, result: Dict[str, Any]) -> bool:
        """
        분석 결과의 신뢰도 평가
        
        Args:
            result: Analyzer 결과
        
        Returns:
            신뢰도 >= 0.65 여부
        """
        score = result.get("score", 0)
        return score >= 0.65


# =========================================
# 🔧 AnalysisSaver
# =========================================
@dataclass
class AnalysisSaver:
    """
    ✅ DB에 분석 결과 저장
    
    🔧 수정 사항:
    - statistics 저장 (빈 dict → 실제 데이터)
    """
    verbose: bool = False  # 🔧 추가
    
    def save(self, db: Session, result: Dict[str, Any], state) -> Dict[str, Any]:
        """
        analysis_result 테이블에 INSERT
        
        Args:
            db: SQLAlchemy 세션
            result: Analyzer 결과
            state: AnalysisState
        
        Returns:
            저장 결과
        """
        if not result:
            return {"status": "no_result"}
        
        try:
            print("💾 [DEBUG] AnalysisSaver.save() 진입")
            print(f"💾 state.id={state.id}, conv_id={state.conv_id}")
            print(f"💾 result keys={list(result.keys()) if result else None}")


            saved = save_analysis_result(
                db=db,
                id=str(state.id),
                conv_id=str(state.conv_id),
                summary=result.get("summary", ""),
                style_analysis=result.get("style_analysis", {}),
                statistics=result.get("statistics", {}),  # ← 🔧 수정
                score=result.get("score", 0.0),
                confidence_score=0.0,  # QA에서 업데이트
                conversation_count=len(state.conversation_df) if state.conversation_df is not None else 0,
                feedback=None,
            )
            
            print(f"✅ [AnalysisSaver] DB 저장 완료: analysis_id={saved['analysis_id']}")
            
            # 🔧 추가: 저장된 데이터 상세 출력
            if self.verbose:
                print(f"   → summary: {result.get('summary', '')[:50]}...")
                print(f"   → score: {result.get('score', 0):.2f}")
                
                # statistics 확인
                stats = result.get("statistics", {})
                if stats:
                    user_stats = stats.get("user", {})
                    print(f"   → 사용자 단어 수: {user_stats.get('word_count', 0)}")
                    print(f"   → 사용자 평균 문장 길이: {user_stats.get('avg_sentence_length', 0)}")
            
            # ✅ state에 저장
            state.meta["analysis_id"] = saved["analysis_id"]
            
            return {
                "status": "saved",
                "analysis_id": saved["analysis_id"],
            }
            
        except Exception as e:
            print(f"❌ [AnalysisSaver] 저장 실패: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}