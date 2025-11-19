# =========================================
# app/agent/Analysis/nodes.py  (FINAL)
# =========================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List
import pandas as pd
import json
from collections import Counter
from dotenv import load_dotenv
load_dotenv()

# ---------------------------------
# NLP / Text Processing
# ---------------------------------
from kiwipiepy import Kiwi
kiwi = Kiwi()

# ---------------------------------
# Dialect + Prosody Normalizer
# ---------------------------------
from app.agent.Analysis.dialect_normalizer import DialectProsodyNormalizer

# ---------------------------------
# LLM
# ---------------------------------
from langchain_openai import ChatOpenAI

# ---------------------------------
# DB CRUD
# ---------------------------------
from app.agent.crud import (
    get_user_by_id,
    save_analysis_result
)

# =========================================================
# TEXT FEATURE UTILITIES
# =========================================================

def extract_content_words(text: str):
    """명사/동사/형용사/부사 중심 내용어 추출"""
    analyses = kiwi.analyze(text)
    if not analyses:
        return []

    morphs = analyses[0][0]
    content_pos = ["NNG", "NNP", "VV", "VA", "MAG"]

    result = []
    for m in morphs:
        if isinstance(m, tuple) and len(m) >= 2:
            form, tag = m[0], m[1]
        elif isinstance(m, dict):
            form, tag = m.get("form"), m.get("tag")
        else:
            continue
        if tag in content_pos:
            result.append(form)
    return result


def calculate_mattr(words: List[str], window: int = 25):
    """Moving-Average Type-Token Ratio"""
    if len(words) < window:
        return len(set(words)) / len(words) if words else 0
    scores = []
    for i in range(len(words) - window + 1):
        win = words[i:i+window]
        scores.append(len(set(win)) / window)
    return sum(scores) / len(scores)


# =========================================================
# 1) Stage 1~6 Analyzer (텍스트 + 음향 + dialect + trigger)
# =========================================================
@dataclass
class Analyzer:
    verbose: bool = False

    def analyze(
        self,
        speaker_segments: List[Dict[str, Any]],
        user_id: int,
        user_gender: str,
        user_age: int
    ):
        """
        Stage 1~6 전체 처리.
        speaker_segments는 Cleaner가 출력한 최종 리스트 그대로.
        """

        # ----------------------------------
        # 1) DataFrame 생성 (speaker, text)
        # ----------------------------------
        df = pd.DataFrame([{
            "speaker": seg["speaker"],
            "text": seg["text"]
        } for seg in speaker_segments])

        # 사용자 화자(SPEAKER_0A 등) 찾기
        user_speaker_label = None
        for seg in speaker_segments:
            if "user_id" in seg and seg["user_id"] == user_id:
                user_speaker_label = seg["speaker"]
                break

        if user_speaker_label is None:
            raise ValueError("❌ user_speaker_label을 찾을 수 없습니다.")

        # ----------------------------------
        # 2) 텍스트 Feature (통계)
        # ----------------------------------
        user_df = df[df["speaker"] == user_speaker_label]
        other_df = df[df["speaker"] != user_speaker_label]

        user_text = " ".join(user_df["text"].tolist())
        other_text = " ".join(other_df["text"].tolist())

        user_words = extract_content_words(user_text)
        other_words = extract_content_words(other_text)

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
        # 4) Surrogate Context
        # ----------------------------------
        surrogate = {
            "relationship_pattern": "neutral",
            "emotional_trajectory_hint": "stable",
        }

        # ----------------------------------
        # 5) Trigger Detection
        # ----------------------------------
        trigger = self._detect_triggers(speaker_segments, prosody_norm)

        # ----------------------------------
        # 6) LLM Stage는 이후 단계에서
        # ----------------------------------
        return {
            "statistics": statistics,
            "prosody_norm": prosody_norm,
            "surrogate": surrogate,
            "trigger": trigger,
            "df": df,
            "user_speaker_label": user_speaker_label,
        }

    # =========================================================
    # 간단한 Trigger 규칙 기반 탐지
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
# 2) Stage 7 LLM STYLE ANALYZER
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
        llm = ChatOpenAI(model="gpt-4o-mini")

        user_text = "\n".join(df[df["speaker"] == user_speaker_label]["text"].tolist())
        full_context = "\n".join(df["text"].tolist())

        prompt = f"""
당신은 대화 분석 전문가입니다.
다음은 전체 대화 내용입니다:

{full_context}

아래는 사용자({user_speaker_label})의 발화만 모은 것입니다:
{user_text}

사용자 정보:
- 나이: {user_age}
- 성별: {user_gender}

텍스트 통계:
{json.dumps(stats, ensure_ascii=False)}

음향 특징 정규화 결과:
{json.dumps(prosody_norm, ensure_ascii=False)}

관계/맥락 추론 힌트:
{json.dumps(surrogate, ensure_ascii=False)}

트리거 정보:
{json.dumps(trigger, ensure_ascii=False)}

위 정보를 바탕으로 다음 JSON 형식으로 사용자의 스타일/감정/어조를 분석하세요.

출력 형식:
{{
  "tone": "...",
  "prosody": "...",
  "emotion_pattern": "...",
  "strengths": "...",
  "risks": "...",
  "politeness": 0.0~1.0,
  "empathy": 0.0~1.0,
  "aggressiveness": 0.0~1.0
}}
"""

        resp = llm.invoke(prompt)
        raw = resp.content if hasattr(resp, "content") else str(resp)

        try:
            return json.loads(raw)
        except:
            return {"raw_text": raw}


# =========================================================
# 3) Stage 8 SUMMARY BUILDER
# =========================================================
@dataclass
class SummaryBuilder:
    def build(self, user_name: str,
              style: Dict[str, Any],
              statistics: Dict[str, Any],
              prosody_norm: Dict[str, Any]):

        tone = style.get("tone", "알 수 없음")
        emotion = style.get("emotion_pattern", "정보 없음")
        mattr = statistics["user"]["mattr"]

        baseline_region = prosody_norm.get("baseline_region", "seoul")

        return (
            f"{user_name}님은 '{tone}' 말투를 보였으며, "
            f"감정 흐름은 '{emotion}' 패턴으로 나타났습니다. "
            f"MATTR {mattr:.3f} 수준으로 언어적 다양성이 안정적이며, "
            f"발화 억양은 '{baseline_region}' 기준에 가까운 것으로 분석됩니다."
        )


# =========================================================
# 4) Stage 9 TEMPERATURE SCORER
# =========================================================
@dataclass
class TemperatureScorer:
    def score(self, style, prosody_norm, trigger):
        politeness = float(style.get("politeness", 0.5))
        empathy = float(style.get("empathy", 0.5))
        aggressiveness = float(style.get("aggressiveness", 0.2))

        deviation = prosody_norm.get("mean_observed_slope", 0)
        stability = 1.0 - min(abs(deviation) / 40, 1)

        # Warmth Base
        warmth_base = (
            0.30 * politeness +
            0.30 * empathy +
            0.20 * stability +
            0.20 * (1 - aggressiveness)
        )

        # Trigger penalty
        intensity = trigger.get("intensity", 0.0)
        warmth_after_trigger = warmth_base * (1 - 0.4 * intensity)

        # LLM Adjustment
        llm_factor = self._adjust_factor(style, prosody_norm, trigger)

        final = warmth_after_trigger * 100 * llm_factor
        return round(max(0, min(100, final)), 2)

    def _adjust_factor(self, style, prosody, trigger):
        llm = ChatOpenAI(model="gpt-4o-mini")

        prompt = f"""
다음 정보를 기반으로 Warmth Score 보정 계수(0.8~1.2)를 숫자만 출력하세요.

스타일:
{json.dumps(style, ensure_ascii=False)}

음향:
{json.dumps(prosody, ensure_ascii=False)}

트리거:
{json.dumps(trigger, ensure_ascii=False)}
"""

        try:
            resp = llm.invoke(prompt)
            value = float(resp.content.strip())
            return min(1.2, max(0.8, value))
        except:
            return 1.0


# =========================================================
# 5) Stage 10 SAVE TO DB
# =========================================================
@dataclass
class AnalysisSaver:
    verbose: bool = False

    def save(self, db, result, conv_id, user_id, conversation_count):
        return save_analysis_result(
            db=db,
            id=user_id,
            conv_id=conv_id,
            summary=result["summary"],
            style_analysis=result["style_analysis"],
            statistics=result["statistics"],
            score=result["temperature_score"],
            confidence_score=0.0,
            conversation_count=conversation_count
        )
