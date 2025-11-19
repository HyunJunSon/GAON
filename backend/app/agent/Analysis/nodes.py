# =========================================
# app/agent/Analysis/nodes.py (FINAL)
# =========================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List
import pandas as pd
import json
from collections import Counter

from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI

# -------------------------------
# 형태소 분석기 (Kiwi)
# -------------------------------
from kiwipiepy import Kiwi
kiwi = Kiwi()

# -------------------------------
# Dialect / Prosody Normalizer
# -------------------------------
from app.agent.Analysis.dialect_normalizer import DialectProsodyNormalizer

# -------------------------------
# CRUD
# -------------------------------
from app.agent.crud import (
    get_user_by_id,
    save_analysis_result
)

# =========================================================
# 1) 텍스트 Feature Utilities
# =========================================================

def extract_content_words(text: str):
    analyses = kiwi.analyze(text)
    if not analyses:
        return []

    morphs = analyses[0][0]  # 형태소 리스트

    content_pos = ["NNG", "NNP", "VV", "VA", "MAG"]

    result = []

    for m in morphs:
        # m이 tuple인지 확인
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
    if len(words) < window:
        return len(set(words)) / len(words) if words else 0
    scores = []
    for i in range(len(words) - window + 1):
        win = words[i:i+window]
        scores.append(len(set(win)) / window)
    return sum(scores) / len(scores)


# =========================================================
# 2) Stage 1~6 Analyzer
# =========================================================
@dataclass
class Analyzer:
    verbose: bool = False

    def analyze(self, df: pd.DataFrame, text_features: dict, audio_features: dict, id: int):
        """
        Stage 1~6 전체 수행
        merged_df = Cleaner가 만들어준 텍스트+audio_features 포함 DF
        """

        # Cleaner가 만든 DF
        merged_df = df.copy()

        # Stage 4(텍스트 feature) 추가
        merged_df["text_features"] = merged_df["speaker"].apply(
            lambda s: text_features.get(s)
        )

        # Stage 5(오디오 feature) 추가
        merged_df["audio_features"] = [
        audio_features[i] if isinstance(audio_features, list) and i < len(audio_features)
        else None
        for i in range(len(merged_df))
    ]

        # -------------------------------
        # Stage 2 — 텍스트 Feature
        # -------------------------------
        user_df = merged_df[merged_df["speaker"] == int(id)]
        other_df = merged_df[merged_df["speaker"] != int(id)]

        user_text = " ".join(user_df["text"].tolist())
        other_text = " ".join(other_df["text"].tolist())

        user_words = extract_content_words(user_text)
        other_words = extract_content_words(other_text)

        user_stats = {
            "token_count": len(user_words),
            "mattr": calculate_mattr(user_words),
            "unique_words": len(set(user_words)),
            "top_words": Counter(user_words).most_common(5),
        }

        other_stats = {
            "token_count": len(other_words),
            "mattr": calculate_mattr(other_words),
        }

        statistics = {
            "user": user_stats,
            "others": other_stats
        }

        # -------------------------------
        # ⭐ NEW — Stage 3~4: Prosody Normalization (dialect_normalizer)
        # -------------------------------
        normalizer = DialectProsodyNormalizer()
        prosody_norm = normalizer.normalize(merged_df)

        # -------------------------------
        # ⭐ NEW — Stage 5: Surrogate Context Reasoning
        # -------------------------------
        surrogate = {
            "relationship_pattern": "neutral",
            "emotional_trajectory_hint": "stable",
        }

        # -------------------------------
        # ⭐ NEW — Stage 6: Trigger Detection
        # -------------------------------
        trigger = {
            "trigger_detected": False,
            "intensity": 0.0,
            "emotion_shift": None
        }

        return {
            "statistics": statistics,
            "prosody_norm": prosody_norm,
            "surrogate": surrogate,
            "trigger": trigger,
        }


# =========================================================
# 3) Stage 7 — LLM 기반 스타일/감정/관계 분석
# =========================================================
@dataclass
class SafetyLLMAnalyzer:
    def analyze(self, merged_df: pd.DataFrame, id: int,
                stats: Dict[str, Any],
                prosody_norm: Dict[str, Any],
                surrogate: Dict[str, Any],
                trigger: Dict[str, Any]):

        llm = ChatOpenAI(model="gpt-4o-mini")

        user_text = "\n".join(merged_df[merged_df["speaker"] == id]["text"].tolist())
        full_context = "\n".join(merged_df["text"].tolist())

        prompt = f"""
다음은 전체 대화 내용입니다:
{full_context}

아래는 사용자(ID={id})의 발화만 모은 내용입니다:
{user_text}

텍스트 통계 분석:
{json.dumps(stats, ensure_ascii=False)}

음향 기반 prosody 정규화 정보:
{json.dumps(prosody_norm, ensure_ascii=False)}

추론 기반 surrogate context:
{json.dumps(surrogate, ensure_ascii=False)}

trigger 탐지 결과:
{json.dumps(trigger, ensure_ascii=False)}

위 분석 결과를 모두 고려하여
사용자의 말투, 억양 패턴, 감정 흐름, 대화 스타일을 JSON으로 분석하세요.

형식:
{{
  "tone": "...",
  "prosody": "...",
  "emotion_pattern": "...",
  "strengths": "...",
  "risks": "..."
}}
"""

        resp = llm.invoke(prompt)
        raw = resp.content if hasattr(resp, "content") else str(resp)

        try:
            return json.loads(raw)
        except:
            return {"raw_text": raw}


# =========================================================
# 4) Stage 8 — Summary Insight 생성
# =========================================================
@dataclass
class SummaryBuilder:
    def build(self, user_name: str,
              style: Dict[str, Any],
              statistics: Dict[str, Any],
              prosody_norm: Dict[str, Any]):

        tone = style.get("tone", "특징 분석 불가")
        emotion = style.get("emotion_pattern", "정보 없음")
        mattr = statistics["user"]["mattr"]

        baseline_region = prosody_norm.get("baseline_region", "unknown")

        summary = (
            f"{user_name}님은 이번 대화에서 '{tone}' 말투를 보였으며, "
            f"감정 흐름은 '{emotion}' 패턴을 보였습니다. "
            f"MATTR {mattr:.3f} 수준으로 언어적 다양성은 안정적이며, "
            f"억양 패턴은 '{baseline_region}' 지역의 특징에 가장 유사한 것으로 분석됩니다."
        )

        return summary


# =========================================================
# 5) Stage 9 — Temperature Score
# =========================================================
@dataclass
class TemperatureScorer:
    def score(
        self,
        style: Dict[str, Any],
        statistics: Dict[str, Any],
        prosody_norm: Dict[str, Any],
        trigger_info: Dict[str, Any]
    ):
        """
        Warmth Score 공식 적용:
        Warmth_Base = 0.30 * Politeness
                    + 0.30 * Empathy
                    + 0.20 * Stability
                    + 0.20 * (1 - Aggressiveness)

        Warmth_Final = Warmth_Base * (1 - 0.4 * Trigger_Intensity)

        Warmth_Score = Warmth_Final * 100 * llm_factor
        """

        # ----- 1) 텍스트 기반 요소 -----
        politeness = float(style.get("politeness", 0.5))
        empathy = float(style.get("empathy", 0.5))
        aggressiveness = float(style.get("aggressiveness", 0.2))

        # ----- 2) 음향 기반 안정성 -----
        stability = 1.0 - min(abs(prosody_norm.get("prosody_deviation", 0)) / 20, 1)

        # ----- 3) Warmth_Base -----
        warmth_base = (
            0.30 * politeness +
            0.30 * empathy +
            0.20 * stability +
            0.20 * (1 - aggressiveness)
        )

        # ----- 4) Trigger 감점 -----
        trigger_intensity = trigger_info.get("intensity", 0.0)
        warmth_after_trigger = warmth_base * (1 - 0.4 * trigger_intensity)

        # ----- 5) LLM 보정 계수 -----
        llm_factor = self._llm_adjust_factor(style, prosody_norm, trigger_info)

        final_score = warmth_after_trigger * 100 * llm_factor

        return round(max(0, min(100, final_score)), 2)

    # =========================================
    # 🔵 NEW — LLM 보정 계수 생성 함수
    # =========================================
    def _llm_adjust_factor(self, style, prosody, trigger):
        llm = ChatOpenAI(model="gpt-4o-mini")

        prompt = f"""
다음은 사용자의 스타일·감정·음향 정보를 요약한 것입니다.

스타일 분석:
{json.dumps(style, ensure_ascii=False)}

음향 분석:
{json.dumps(prosody, ensure_ascii=False)}

트리거 분석:
{json.dumps(trigger, ensure_ascii=False)}

위 정보를 기반으로 Warmth Score의 보정 계수(0.8~1.2 사이)를 결정하세요.
숫자만 출력하세요.
"""
        try:
            resp = llm.invoke(prompt)
            value = float(resp.content.strip())
            return float(min(1.2, max(0.8, value)))
        except:
            return 1.0  # fallback


# =========================================================
# 6) DB 저장 Stage
# =========================================================
@dataclass
class AnalysisSaver:
    verbose: bool = False

    def save(self, db: Session, result: Dict[str, Any], state):
        """
        summary / style_analysis / statistics / score 저장
        """

        return save_analysis_result(
            db=db,
            id=state.id,
            conv_id=state.conv_id,
            summary=result["summary"],
            style_analysis=result["style_analysis"],
            statistics=result["statistics"],
            score=result["temperature_score"],
            confidence_score=0.0,
            conversation_count=len(state.conversation_df)
        )
