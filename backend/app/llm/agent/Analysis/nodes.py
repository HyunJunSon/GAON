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
from kiwipiepy import Kiwi
from app.llm.agent.Analysis.dialect_normalizer import DialectProsodyNormalizer

# ✅ Kiwi 초기화
kiwi = Kiwi()

# =========================================================
# TEXT FEATURE UTILITIES
# =========================================================

def extract_content_words(text: str):
    """Kiwi Token 객체를 직접 처리하여 내용어 추출"""
    analyses = kiwi.analyze(text)
    if not analyses:
        return []
    
    morphs = analyses[0][0]   # Token 객체 리스트
    content_prefixes = ("NN", "VV", "VA", "MAG", "IC", "NP", "XR", "VX", "SL")
    
    result = []
    for m in morphs:
        if m.tag.startswith(content_prefixes):
            result.append(m.form)
    
    return result


def calculate_mattr(words: List[str], window: int = 25):
    """Moving-Average Type-Token Ratio (MATTR)"""
    if len(words) < window:
        return len(set(words)) / len(words) if words else 0
    
    scores = []
    for i in range(len(words) - window + 1):
        win = words[i:i + window]
        scores.append(len(set(win)) / window)
    
    return sum(scores) / len(scores)


# ✅ CRUD 함수 import
from app.llm.agent.crud import (
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
@dataclass
class Analyzer:
    verbose: bool = False

    def analyze(
        self,
        speaker_segments: List[Dict[str, Any]],
        user_id: int,
        user_gender: str,
        user_age: int,
        user_name: str,
        user_speaker_label: str,
        other_speaker_label: str,
        other_display_name: str
    ):

        # ----------------------------------
        # 1) DataFrame 생성
        # ----------------------------------
        df = pd.DataFrame([{
            "speaker": seg["speaker"],
            "text": seg["text"]
        } for seg in speaker_segments])

        # 🔍 DEBUG — DF 전체 출력
        print("\n[DEBUG] DF created:")
        print(df.head(10))

        # ----------------------------------
        # 2) 텍스트 Feature
        # ----------------------------------
        user_df = df[df["speaker"] == user_speaker_label]
        other_df = df[df["speaker"] != user_speaker_label]

        print("\n[DEBUG] user_df:", user_df.head())
        print("[DEBUG] other_df:", other_df.head())

        user_text = " ".join(user_df["text"].tolist())
        other_text = " ".join(other_df["text"].tolist())

        print("\n[DEBUG] user_text:", user_text)
        print("[DEBUG] other_text:", other_text)

        user_words = extract_content_words(user_text)
        other_words = extract_content_words(other_text)

        print("\n[DEBUG] user_words:", user_words)
        print("[DEBUG] other_words:", other_words)

        statistics = {
            "user": {
                "token_count": len(user_words),
                "mattr": calculate_mattr(user_words),
                "unique_words": len(set(user_words)),
                "top_words": Counter(user_words).most_common(5),
            },
            "others": {
                "token_count": len(other_words),
                "mattr": calculate_mattr(other_words),
            }
        }

        # ----------------------------------
        # 3) Prosody Normalization
        # ----------------------------------
        normalizer = DialectProsodyNormalizer()
        prosody_norm = normalizer.normalize(speaker_segments)

        # ----------------------------------
        # 4) Surrogate (감정 흐름 + 반응성)
        # ----------------------------------
# (1) 감정 흐름 분석: prosody_norm의 slope 기반
        slopes = [
            t.get("observed_slope")
            for t in prosody_norm.get("turn_prosody", [])
            if t.get("observed_slope") is not None
        ]

        if slopes:
            avg_slope = sum(slopes) / len(slopes)
            if avg_slope > 5:
                emotion_trajectory = "rising (감정 상승)"
            elif avg_slope < -5:
                emotion_trajectory = "falling (감정 하강)"
            else:
                emotion_trajectory = "stable (안정적)"
        else:
            emotion_trajectory = "unknown"

        # (2) 반응성 분석: 발화 간 텀(시간), 발화 길이 기반
        from numpy import mean

        durations = []
        for seg in speaker_segments:
            start = seg.get("start")
            end = seg.get("end")
            if start is not None and end is not None:
                durations.append(end - start)

        if durations:
            avg_len = mean(durations)
            if avg_len > 5:
                responsiveness = "slow"
            elif avg_len < 1.5:
                responsiveness = "fast"
            else:
                responsiveness = "moderate"
        else:
            responsiveness = "unknown"

        # (3) 발화 비율 기반 주도성
        user_count = len(user_df)
        other_count = len(other_df)
        dominance_ratio = user_count / (user_count + other_count + 1e-6)

        if dominance_ratio > 0.65:
            dominance = "high"
        elif dominance_ratio < 0.35:
            dominance = "low"
        else:
            dominance = "balanced"

        # 최종 Surrogate 구성
        surrogate = {
            "emotion_trajectory": emotion_trajectory,
            "responsiveness": responsiveness,
            "dominance": dominance,
            "relationship_pattern": "neutral",  # 기본값 유지
        }

        # ----------------------------------
        # 5) Trigger Detection
        # ----------------------------------
        trigger = self._detect_triggers(speaker_segments, prosody_norm)

        # ----------------------------------
        # 6) LLM Style Analysis
        # ----------------------------------
        style_analyzer = SafetyLLMAnalyzer()
        style = style_analyzer.analyze(
            df=df,
            user_speaker_label=user_speaker_label,
            user_gender=user_gender,
            user_age=user_age,
            stats=statistics,
            prosody_norm=prosody_norm,
            surrogate=surrogate,
            trigger=trigger
        )

        # ----------------------------------
        # 7) Temperature Score
        # ----------------------------------
        scorer = TemperatureScorer()
        score = scorer.score(style, prosody_norm, trigger)

        # ----------------------------------
        # 8) Summary
        # ----------------------------------
        summary_builder = SummaryBuilder()
        summary = summary_builder.build(
            user_name=user_name if user_name else "사용자",
            df=df,
            user_speaker_label=user_speaker_label,
            user_gender=user_gender,
            user_age=user_age,
            style=style,
            statistics=statistics,
            prosody_norm=prosody_norm,
            surrogate=surrogate,
            trigger=trigger
        )

        return {
            "statistics": statistics,
            "prosody_norm": prosody_norm,
            "surrogate": surrogate,
            "trigger": trigger,
            "style": style,
            "score": score,
            "summary": summary,
            "df": df,
        }


    # =========================================================
    # Trigger (deviation 기반 rule)
    # =========================================================
    def _detect_triggers(self, segments, prosody_norm):
        deviations = [
            r.get("emotional_deviation", 0)
            for r in prosody_norm.get("turn_prosody", [])
            if r.get("emotional_deviation") is not None
        ]

        if not deviations:
            return {"trigger_detected": False, "intensity": 0.0, "emotion_shift": None}

        max_dev = max(abs(d) for d in deviations)

        trigger_detected = max_dev > 20
        intensity = min(max_dev / 40, 1)

        return {
            "trigger_detected": trigger_detected,
            "intensity": round(float(intensity), 3),
            "emotion_shift": "abrupt_change" if trigger_detected else "stable"
        }


# =========================================================
# 2) Stage 7 — LLM STYLE ANALYZER
# =========================================================

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
                    print(f"   → 사용자 단어 수: {user_stats.get('token_count', 0)}")
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

# =========================================================
# SafetyLLMAnalyzer - LLM 기반 스타일 분석
# =========================================================
@dataclass
class SafetyLLMAnalyzer:
    def analyze(
        self,
        df: pd.DataFrame,
        user_speaker_label: str,
        user_gender: str,
        user_age: int,
        stats: Dict[str, Any],
        prosody_norm: Dict[str, Any],
        surrogate: Dict[str, Any],
        trigger: Dict[str, Any]
    ):
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)

        user_text = "\n".join(df[df["speaker"] == user_speaker_label]["text"].tolist())
        full_context = "\n".join(df["text"].tolist())

        prompt = f"""
당신은 대화 분석 전문가입니다. 한국어로 답하세요.
다음은 전체 대화 내용입니다. 전체 발화에서 대화의 맥락을 이해한 후, 맥락에 근거하여 사용자 정보를 추가적으로 확인하고 사용자의 발화 스타일을 JSON으로 출력하세요.

{full_context}

사용자({user_speaker_label}) 발화만:
{user_text}

사용자 정보:
- 나이: {user_age}
- 성별: {user_gender}

텍스트 통계:
{json.dumps(stats, ensure_ascii=False)}

음향·억양 분석:
{json.dumps(prosody_norm, ensure_ascii=False)}

맥락 힌트:
{json.dumps(surrogate, ensure_ascii=False)}

트리거 정보:
{json.dumps(trigger, ensure_ascii=False)}

다음을 JSON으로 출력:
{{
  "tone": "...",
  "prosody": "...",
  "emotion_pattern": "...",
  "strengths": "...",
  "risks": "...",
  "politeness": 0.0,
  "empathy": 0.0,
  "aggressiveness": 0.0
}}
"""

        resp = llm.invoke(prompt)
        raw = resp.content if hasattr(resp, "content") else str(resp)

        try:
            return json.loads(raw)
        except:
            return {"raw_text": raw}


# =========================================================
# SummaryBuilder - LLM 기반 요약 생성
# =========================================================
@dataclass
class SummaryBuilder:
    def build(
        self,
        user_name: str,
        df: pd.DataFrame,
        user_speaker_label: str,
        user_gender: str,
        user_age: int,
        style: Dict[str, Any],
        statistics: Dict[str, Any],
        prosody_norm: Dict[str, Any],
        surrogate: Dict[str, Any],
        trigger: Dict[str, Any],
    ):
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, api_key=settings.openai_api_key)
        full_context = "\n".join(df["text"].tolist())
        user_text = "\n".join(df[df["speaker"] == user_speaker_label]["text"].tolist())

        prompt = f"""
당신은 대화 분석 리포트를 작성하는 전문가입니다.
아래 제공된 전체 발화, {user_name}님 정보, 텍스트·음향 분석 결과를 기반으로
**정해진 리포트 형식 그대로** 고급 분석 보고서를 작성하십시오.
보고서는 반드시 1200자 이상이며, JSON은 절대 출력하지 않습니다.

⚠️ 중요:
- 아래 구조, 제목, 구분선 모두 그대로 출력
- "사용자"라는 단어를 쓰지 말고 반드시 **"{user_name}님"**이라고 지칭
- 데이터 나열이 아닌 ‘해석 중심’으로 작성
- 단정적 평가 금지 (관찰 기반 서술)

============================================================================
📊 대화 분석 종합 리포트
============================================================================

[분석 대상] {user_name}님  
[대화 규모] 전체 발화 수: {len(df)}회  
({user_name}님 발화: {len(df[df["speaker"] == user_speaker_label])}회,  
상대방 발화: {len(df[df["speaker"] != user_speaker_label])}회)

----------------------------------------------------------------------------
🎯 대화의 온도: (prosody_norm 기반 정서적 안정도 해석)
----------------------------------------------------------------------------

📈 통계 분석  
• {user_name}님 총 단어 수: {statistics.get("token_count_user")}  
• 평균 문장 길이: {statistics.get("avg_sentence_len_user")}단어  
• 고유 단어 수: {statistics.get("unique_words_user")}  

• 상대방 총 단어 수: {statistics.get("token_count_other")}  
• 상대방 평균 문장 길이: {statistics.get("avg_sentence_len_other")}단어  

• 비교 분석: {user_name}님의 발화량과 상대방 발화량의 차이 및 패턴 설명

🤖 AI 해석:  
위 통계를 기반으로 {user_name}님의 표현 방식, 어휘 다양성(MATTR 포함), 문장 구성 습관을  
6~7문장 이상 전문가 관점에서 해석해 서술하세요.

----------------------------------------------------------------------------
🗣️ 말투 특징 분석
----------------------------------------------------------------------------

{user_name}님의 말투/언어 스타일을 아래 요소 중심으로 자연스럽게 설명:
- 말투의 전체 분위기  
- 존댓말/반말 사용 경향  
- 간결성·직설성·완곡성  
- prosody_norm 기반 억양·속도·리듬  
- 반복되는 패턴 또는 특징  

----------------------------------------------------------------------------
💬 대화 성향 및 감정 표현
----------------------------------------------------------------------------

전체 맥락(full_context)에서 {user_name}님의 감정 흐름과 표현 방식을  
다음 기준으로 10문장 이상 해석:
- 감정이 드러나는 순간  
- 감정 표현의 깊이/방식  
- 정서적 안정감 또는 취약성  
- 특정 주제에서의 반응성 (trigger 기반)  
- 상대방과의 관계적 흐름 (surrogate 기반)  
- 말하기를 통해 드러나는 내적 상태  

----------------------------------------------------------------------------
🎯 주요 관심사
----------------------------------------------------------------------------

전체 발화에서 {user_name}님이 반복적으로 드러낸 관심사·가치·주요 주제를  
5~8문장으로 서술하세요.

----------------------------------------------------------------------------
📊 상대방과의 비교
----------------------------------------------------------------------------

{user_name}님과 상대방의 대화 스타일 차이를  
아래 기준으로 10문장 이상 분석:
- 문장 길이  
- 말하기 비중  
- 대화 주도성  
- 질문·응답 패턴  
- 감정 표현 방식  
- 상호작용 리듬의 차이  

----------------------------------------------------------------------------
🤖 AI 종합 분석
----------------------------------------------------------------------------

{user_name}님의 커뮤니케이션 강점·특징·정서적 자원  
그리고 관계 개선 또는 표현 확장 측면에서의 가능성을  
전문가 코칭 스타일로 12문장 이상 자연스럽게 서술하십시오.

============================================================================

📌 추가 작성 규칙:
- bullet은 사용 가능하나 전체는 자연스럽게 이어지는 서술형 보고서일 것
- 데이터 값은 나열이 아니라 반드시 의미를 해석해 서술
- JSON 출력 금지
- 전체 분량 1200자 이상 필수
- "사용자"라는 단어 사용 금지 → 반드시 **{user_name}님**으로 지칭

============================================================================

# 전체 대화 내용
{full_context}

# {user_name}님 발화({user_speaker_label})
{user_text}

# 텍스트 통계
{json.dumps(statistics, ensure_ascii=False, indent=2)}

# Prosody 분석
{json.dumps(prosody_norm, ensure_ascii=False, indent=2)}

# 스타일 분석 결과
{json.dumps(style, ensure_ascii=False, indent=2)}

# Surrogate 정보
{json.dumps(surrogate, ensure_ascii=False, indent=2)}

# Trigger 정보
{json.dumps(trigger, ensure_ascii=False, indent=2)}
"""


        resp = llm.invoke(prompt)
        summary = resp.content if hasattr(resp, "content") else str(resp)
        return summary.strip()


# =========================================================
# TemperatureScorer - 온도 점수 계산
# =========================================================
@dataclass
class TemperatureScorer:
    def score(self, style, prosody_norm, trigger):
        politeness = float(style.get("politeness", 0.5))
        empathy = float(style.get("empathy", 0.5))
        aggressiveness = float(style.get("aggressiveness", 0.2))

        deviation = prosody_norm.get("mean_observed_slope", 0)
        stability = 1.0 - min(abs(deviation) / 60, 1)

        warmth_base = (
            0.35 * politeness +
            0.35 * empathy +
            0.15 * stability +
            0.15 * (1 - aggressiveness)
        )

        intensity = trigger.get("intensity", 0.0)
        warmth_after_trigger = warmth_base * (1 - 0.2 * intensity)

        final_score = max(30, warmth_after_trigger * 100)

        return round(min(100, final_score), 2)
