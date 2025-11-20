# =========================================
# app/agent/Analysis/nodes.py  (FINAL + DEBUG + FIXED)
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
from app.agent.crud import save_analysis_result


# =========================================================
# TEXT FEATURE UTILITIES
# =========================================================

def extract_content_words(text: str):
    """Kiwi Token 객체를 직접 처리하여 내용어 추출"""

    analyses = kiwi.analyze(text)

    if not analyses:
        return []

    # Kiwi 결과 형식: [( [Token(), Token(), ...], score )]
    morphs = analyses[0][0]   # Token 객체 리스트

    # 포함할 태그
    content_prefixes = ("NN", "VV", "VA", "MAG", "IC", "NP", "XR", "VX", "SL")

    result = []
    for m in morphs:
        tag = m.tag
        form = m.form

        # prefix로 필터 (예: NNG, NNP, VV+어미 등 모두 잡힘)
        if tag.startswith(content_prefixes):
            result.append(form)

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


# =========================================================
# 1) Stage 1~6 Analyzer (텍스트 + prosody + trigger)
# =========================================================
@dataclass
class Analyzer:
    verbose: bool = False

    def analyze(
        self,
        speaker_segments: List[Dict[str, Any]],
        user_id: int,
        user_gender: str,
        user_age: int,
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
        # 4) Surrogate (간단한 맥락 힌트)
        # ----------------------------------
        surrogate = {
            "relationship_pattern": "neutral",
            "emotional_trajectory_hint": "stable",
        }

        # ----------------------------------
        # 5) Trigger Detection
        # ----------------------------------
        trigger = self._detect_triggers(speaker_segments, prosody_norm)

        return {
            "statistics": statistics,
            "prosody_norm": prosody_norm,
            "surrogate": surrogate,
            "trigger": trigger,
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

        # 🔍 DEBUG — LLM 입력 문장 확인
        print("\n[DEBUG] LLMAnalyzer user_text:\n",
              "\n".join(df[df["speaker"] == user_speaker_label]["text"].tolist()))
        print("\n[DEBUG] LLMAnalyzer full_context:\n",
              "\n".join(df["text"].tolist()))

        llm = ChatOpenAI(model="gpt-4o-mini")

        user_text = "\n".join(df[df["speaker"] == user_speaker_label]["text"].tolist())
        full_context = "\n".join(df["text"].tolist())

        # ----------------------------
        # 🔥 PROMPT 생성
        # ----------------------------
        prompt = f"""
당신은 대화 분석 전문가입니다.한국어로 답하세요.
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

        # ----------------------------
        # 🔥 LLM에게 전달되는 Prompt 전체를 완전 출력
        # ----------------------------
        print("\n================= [DEBUG] LLM PROMPT INPUT =================")
        print(prompt)
        print("============================================================\n")

        # ----------------------------
        # LLM 호출
        # ----------------------------
        resp = llm.invoke(prompt)
        raw = resp.content if hasattr(resp, "content") else str(resp)

        try:
            return json.loads(raw)
        except:
            return {"raw_text": raw}


# =========================================================
# 3) Stage 8 — LLM SUMMARY BUILDER 
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

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
        full_context = "\n".join(df["text"].tolist())
        user_text = "\n".join(df[df["speaker"] == user_speaker_label]["text"].tolist())

        # ---------------------------------------------------
        # ★ SummaryBuilder Prompt
        # ---------------------------------------------------
        prompt = f"""
당신은 대화 분석 리포트를 작성하는 전문가입니다.
다음은 전체 대화 맥락과 분석 정보입니다.
전체 맥락을 기반으로 종합적인 분석 리포트를 구조화해서 고급 인사이트를 작성하세요. 분량은 500~700자 내외로 합니다.

# 전체 대화 내용
{full_context}

# 사용자({user_speaker_label}) 발화만
{user_text}

# 사용자 정보
- 이름: {user_name}
- 나이: {user_age}
- 성별: {user_gender}

# 스타일 분석 결과
{json.dumps(style, ensure_ascii=False, indent=2)}

# 텍스트 통계
{json.dumps(statistics, ensure_ascii=False, indent=2)}

# Prosody·억양 분석
{json.dumps(prosody_norm, ensure_ascii=False, indent=2)}

# Surrogate 관계 힌트
{json.dumps(surrogate, ensure_ascii=False, indent=2)}

# Trigger 정보
{json.dumps(trigger, ensure_ascii=False, indent=2)}

📌 작성 규칙:
- 첫 문장은 {user_name}님의 전체 말하기 핵심 특징을 요약
- 대화 full_context에서 드러난 감정적/맥락적 특징을 문장으로 풀어서 반드시 반영
- 텍스트 통계의 mattr의 정의와 점수에 대한 해석 반영 (Moving-Average Type-Token Ratio (MATTR)
    if len(words) < window:
        return len(set(words)) / len(words) if words else 0

    scores = []
    for i in range(len(words) - window + 1):
        win = words[i:i + window]
        scores.append(len(set(win)) / window)

    return sum(scores) / len(scores))
- tone, emotion, prosody, 상호작용 특징, 위험 요소를 요소 그대로 작성하는 것이 아닌, 전문가가 풀어서 해설하듯이 자연스럽게 서술
- 분석 결과에 대한 근거를 해석해서 서술
- 하나의 자연스러운 문단으로 작성하되, 평가한다는 문장이나 단언하는 표현은 지양
"""

        resp = llm.invoke(prompt)
        summary = resp.content if hasattr(resp, "content") else str(resp)
        return summary.strip()


# =========================================================
# 4) Stage 9 — TEMPERATURE SCORER
# =========================================================
@dataclass
class TemperatureScorer:
    def score(self, style, prosody_norm, trigger):
        politeness = float(style.get("politeness", 0.5))
        empathy = float(style.get("empathy", 0.5))
        aggressiveness = float(style.get("aggressiveness", 0.2))

        # 안정성 영향 완화
        deviation = prosody_norm.get("mean_observed_slope", 0)
        stability = 1.0 - min(abs(deviation) / 60, 1)   # 40 → 60

        # 전체 온도 기반 (점수 높게 보정)
        warmth_base = (
            0.35 * politeness +        # 0.30 → 0.35
            0.35 * empathy +           # 0.30 → 0.35
            0.15 * stability +         # 0.20 → 0.15
            0.15 * (1 - aggressiveness) # 0.20 → 0.15
        )

        # Trigger 패널티 완화 (40% → 20%)
        intensity = trigger.get("intensity", 0.0)
        warmth_after_trigger = warmth_base * (1 - 0.2 * intensity)

        # 바닥은 30점 보장
        final_score = max(30, warmth_after_trigger * 100)

        return round(min(100, final_score), 2)



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
