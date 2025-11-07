# app/agent/Analysis/nodes.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
from app.core.config import settings
from langchain_openai import ChatOpenAI
import pandas as pd
from sqlalchemy.orm import Session

# ✅ CRUD 함수 import
from app.agent.crud import (
    get_user_by_id,
    get_family_by_id,
    save_analysis_result,
)


# =========================================
# ✅ UserFetcher (DB 연동) - 수정 없음
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
            conv_state: AnalysisState (user_id 포함)
        
        Returns:
            사용자 정보 Dict
        """
        user_id = conv_state.user_id
        
        if not user_id:
            raise ValueError("❌ UserFetcher: user_id가 없습니다.")
        
        # ✅ DB 조회
        user = get_user_by_id(db, user_id)
        
        if not user:
            raise ValueError(f"❌ UserFetcher: user_id={user_id}를 찾을 수 없습니다.")
        
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
# ✅ RelationResolver_DB (비활성화) - 수정 없음
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
# ✅ RelationResolver_LLM (기존 유지) - 수정 없음
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
예: [{{"speaker":"1","relation":"엄마"}}, {{"speaker":"2","relation":"아들"}}]
"""
        
        try:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            
            if self.verbose:
                print(f"🧠 [RelationResolver_LLM] 응답: {content[:200]}")
            
            # ✅ 간단한 fallback
            return [
                {"speaker": "1", "relation": "참석자1"},
                {"speaker": "2", "relation": "참석자2"}
            ]
            
        except Exception as e:
            print(f"⚠️ Relation LLM 실패: {e}")
            return []


# =========================================
# 🔧 Analyzer (사용자 중심 분석) - 전체 수정
# =========================================
@dataclass
class Analyzer:
    """
    감정/스타일/통계 분석
    
    🔧 수정 사항:
    1. user_id 파라미터 추가
    2. 사용자만 style_analysis에 저장
    3. 사용자 vs 상대방 비교 통계
    4. score는 사용자 말하기 점수
    """
    verbose: bool = False

    # 🔧 수정: user_id 파라미터 추가
    def analyze(
        self,
        conversation_df: pd.DataFrame,
        relations: List[Dict[str, Any]],
        user_id: int  # ← 🔧 추가
    ) -> Dict[str, Any]:
        """
        LLM으로 대화 분석 (사용자 중심)
        
        🔧 수정 사항:
        - user_id 기준 분석
        - 전체 대화 맥락 파악
        - 사용자 vs 상대방 비교
        
        Args:
            conversation_df: 대화 DataFrame
            relations: 관계 정보
            user_id: 분석 의뢰 사용자 ID
        
        Returns:
            분석 결과 (DB 스키마 준수)
        """
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)
        
        # =========================================
        # 🔧 추가: 사용자/상대방 DataFrame 분리
        # =========================================
        # 이유: 사용자 중심 분석 + 비교 분석
        # =========================================
        
        user_df = conversation_df[conversation_df["speaker"] == str(user_id)]
        others_df = conversation_df[conversation_df["speaker"] != str(user_id)]
        
        if user_df.empty:
            raise ValueError(f"❌ user_id={user_id}의 발화가 없습니다!")
        
        if self.verbose:
            print(f"   👤 사용자 발화: {len(user_df)}개")
            print(f"   👥 상대방 발화: {len(others_df)}개")
        
        # =========================================
        # 🔧 수정: statistics 생성 (사용자 vs 상대방 비교)
        # =========================================
        # 이유: 사용자의 대화 패턴을 상대와 비교
        # =========================================
        
        # 사용자 통계
        user_texts = " ".join(user_df["text"].tolist())
        user_words = user_texts.split()
        
        user_stats = {
            "word_count": len(user_words),
            "avg_sentence_length": round(len(user_words) / len(user_df), 1),
            "unique_words": len(set(user_words)),
            "top_words": self._get_top_words(user_texts, top_n=5)
        }
        
        # 상대방 통계
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
        
        # 비교 분석
        comparison = self._generate_comparison(user_stats, others_stats)
        
        # 🔧 수정: statistics 구조 변경
        statistics = {
            "user": user_stats,
            "others": others_stats,
            "comparison": comparison
        }
        
        if self.verbose:
            print(f"   📊 [Statistics] 사용자 단어: {user_stats['word_count']}, "
                  f"상대방 단어: {others_stats['word_count']}")
        
        # =========================================
        # 🔧 수정: style_analysis 생성 (사용자만)
        # =========================================
        # 이유: 사용자의 말하기 스타일 분석
        # 맥락: 전체 대화 포함하여 분석
        # =========================================
        
        # 전체 대화 맥락
        full_context = "\n".join([
            f"화자 {row['speaker']}: {row['text']}"
            for _, row in conversation_df.iterrows()
        ])
        
        # 사용자 발화
        user_texts_joined = "\n".join(user_df["text"].tolist())
        
        # 🔧 수정: LLM 프롬프트 개선
        style_prompt = f"""
다음은 대화 전체 맥락과 분석 대상 사용자의 발화입니다.
**사용자 ID {user_id}**의 말투, 성향, 관심사를 분석해주세요.

**전체 대화 맥락:**
{full_context[:500]}...

**분석 대상 사용자 (ID: {user_id})의 발화:**
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
  "주요_관심사": "대화 주제와 관심사",
  "대화_비교_분석": "상대방 대비 사용자의 대화 특징 (간결함, 상세함, 주도성 등)"
}}
"""
        
        try:
            response = llm.invoke(style_prompt)
            content = response.content if hasattr(response, "content") else str(response)
            
            if self.verbose:
                print(f"   🗣️ [Style Analysis] 사용자: {content[:100]}...")
            
            # JSON 파싱 시도
            import json
            try:
                user_analysis = json.loads(content)
            except:
                # JSON 파싱 실패 시 fallback
                user_analysis = {
                    "말투_특징_분석": content[:100],
                    "대화_성향_및_감정_표현": "분석 중",
                    "주요_관심사": "분석 중",
                    "대화_비교_분석": "분석 중"
                }
            
            # 🔧 수정: user_id만 저장
            style_analysis = {
                str(user_id): user_analysis
            }
            
        except Exception as e:
            print(f"⚠️ 사용자 스타일 분석 LLM 실패: {e}")
            style_analysis = {
                str(user_id): {
                    "말투_특징_분석": "분석 실패",
                    "대화_성향_및_감정_표현": "분석 실패",
                    "주요_관심사": "분석 실패",
                    "대화_비교_분석": "분석 실패"
                }
            }
        
        # =========================================
        # 3️⃣ summary 생성 (전체 대화 요약) - 기존 유지
        # =========================================
        
        summary_prompt = f"""
다음 대화를 100-200자로 요약해주세요. 주요 주제와 분위기를 포함해주세요.

대화:
{full_context}

요약 (100-200자):
"""
        
        try:
            response = llm.invoke(summary_prompt)
            summary = response.content if hasattr(response, "content") else str(response)
            summary = summary.strip()
            
            if self.verbose:
                print(f"   📝 [Summary] {summary[:50]}...")
                
        except Exception as e:
            print(f"⚠️ 요약 LLM 실패: {e}")
            summary = "대화 요약 생성 실패"
        
        # =========================================
        # 🔧 수정: score 계산 (사용자 말하기 점수)
        # =========================================
        # 이유: 사용자의 말하기 능력 평가
        # =========================================
        
        score = self._calculate_user_score(user_stats, others_stats, user_analysis)
        
        if self.verbose:
            print(f"   🎯 [Score] 사용자 말하기 점수: {score:.2f}")
        
        # =========================================
        # ✅ 최종 결과 반환
        # =========================================
        
        return {
            "summary": summary,
            "style_analysis": style_analysis,
            "statistics": statistics,
            "score": score,
        }
    
    # 🔧 추가: 비교 분석 텍스트 생성
    def _generate_comparison(self, user_stats: Dict, others_stats: Dict) -> str:
        """
        사용자 vs 상대방 비교 분석 텍스트 생성
        
        Args:
            user_stats: 사용자 통계
            others_stats: 상대방 통계
        
        Returns:
            비교 분석 텍스트
        """
        comparisons = []
        
        # 단어 수 비교
        if others_stats["word_count"] > 0:
            word_ratio = user_stats["word_count"] / others_stats["word_count"]
            if word_ratio < 0.7:
                comparisons.append("사용자는 상대방보다 말을 적게 함")
            elif word_ratio > 1.3:
                comparisons.append("사용자는 상대방보다 말을 많이 함")
            else:
                comparisons.append("사용자와 상대방의 대화량이 비슷함")
        
        # 문장 길이 비교
        if others_stats["avg_sentence_length"] > 0:
            len_diff = user_stats["avg_sentence_length"] - others_stats["avg_sentence_length"]
            if len_diff < -2:
                comparisons.append("사용자는 짧은 문장을 선호")
            elif len_diff > 2:
                comparisons.append("사용자는 긴 문장을 선호")
        
        return ", ".join(comparisons) if comparisons else "비교 데이터 부족"
    
    # 🔧 추가: 사용자 말하기 점수 계산
    def _calculate_user_score(
        self,
        user_stats: Dict,
        others_stats: Dict,
        user_analysis: Dict
    ) -> float:
        """
        사용자 말하기 점수 계산
        
        Args:
            user_stats: 사용자 통계
            others_stats: 상대방 통계
            user_analysis: 사용자 스타일 분석
        
        Returns:
            말하기 점수 (0.0 ~ 1.0)
        
        평가 기준:
        1. 어휘 다양성 (unique_words / word_count)
        2. 대화 참여도 (user vs others 비율)
        3. 문장 구조 (avg_sentence_length)
        """
        score_components = []
        
        # 1. 어휘 다양성 (0 ~ 0.4점)
        if user_stats["word_count"] > 0:
            vocab_diversity = user_stats["unique_words"] / user_stats["word_count"]
            vocab_score = min(0.4, vocab_diversity * 0.8)
            score_components.append(vocab_score)
        
        # 2. 대화 참여도 (0 ~ 0.3점)
        if others_stats["word_count"] > 0:
            participation_ratio = user_stats["word_count"] / (user_stats["word_count"] + others_stats["word_count"])
            # 0.4 ~ 0.6 비율이 이상적
            if 0.4 <= participation_ratio <= 0.6:
                participation_score = 0.3
            else:
                participation_score = 0.3 * (1 - abs(participation_ratio - 0.5) * 2)
            score_components.append(participation_score)
        
        # 3. 문장 구조 (0 ~ 0.3점)
        # 5 ~ 10 단어가 이상적
        avg_len = user_stats["avg_sentence_length"]
        if 5 <= avg_len <= 10:
            structure_score = 0.3
        elif avg_len < 5:
            structure_score = 0.3 * (avg_len / 5)
        else:
            structure_score = 0.3 * (10 / avg_len)
        score_components.append(structure_score)
        
        # 최종 점수
        final_score = sum(score_components)
        
        # 0.5 ~ 1.0 범위로 정규화
        normalized_score = 0.5 + (final_score * 0.5)
        
        return round(min(1.0, max(0.0, normalized_score)), 2)
    
    def _get_top_words(self, text: str, top_n: int = 5) -> List[str]:
        """
        빈도 높은 단어 추출 (한글 기준)
        
        Args:
            text: 전체 텍스트
            top_n: 상위 N개
        
        Returns:
            빈도 높은 단어 리스트
        """
        from collections import Counter
        import re
        
        # 한글만 추출
        words = re.findall(r'[가-힣]+', text)
        
        # 1글자 단어 제외, 조사 제외 (간단한 필터)
        words = [w for w in words if len(w) >= 2]
        
        # 빈도 계산
        word_counts = Counter(words)
        
        # 상위 N개 추출
        top_words = [word for word, count in word_counts.most_common(top_n)]
        
        return top_words


# =========================================
# ✅ ScoreEvaluator (기존 유지) - 수정 없음
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
# 🔧 AnalysisSaver (DB 연동) - 부분 수정
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
            # 🔧 수정: statistics 실제 데이터 저장
            saved = save_analysis_result(
                db=db,
                user_id=str(state.user_id),
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