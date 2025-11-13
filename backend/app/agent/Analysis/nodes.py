# app/agent/Analysis/nodes.py 
# =========================================
# 형태소 기반 MATTR + 화자별 other 통계 분리
# =========================================

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

# 🧩 형태소 분석기 추가
from konlpy.tag import Okt
okt = Okt()

# =========================================
# CRUD import
# =========================================
from app.agent.crud import (
    get_user_by_id,
    save_analysis_result,
)


# =========================================
# 🔧 CONTENT WORD EXTRACTOR
# =========================================
def extract_content_words_korean(text: str) -> List[str]:
    """한국어 내용어(명사·동사·형용사·부사)만 추출"""
    morphs = okt.pos(text, stem=True)
    content_pos = ["Noun", "Verb", "Adjective", "Adverb"]
    return [word for word, pos in morphs if pos in content_pos]


def calculate_mattr_korean(words: List[str], window_size: int = 25) -> float:
    """한국어 내용어 기반 MATTR 계산"""
    if len(words) < window_size:
        return len(set(words)) / len(words) if words else 0.0

    ttr_vals = []
    for i in range(len(words) - window_size + 1):
        window = words[i:i + window_size]
        ttr_vals.append(len(set(window)) / window_size)

    return sum(ttr_vals) / len(ttr_vals)


# =========================================
# UserFetcher
# =========================================
@dataclass
class UserFetcher:
    def fetch(self, db: Session, conv_state) -> Dict[str, Any]:
        id = conv_state.id
        if not id:
            raise ValueError("❌ UserFetcher: id가 없습니다.")

        user = get_user_by_id(db, id)
        if not user:
            raise ValueError(f"❌ UserFetcher: id={id}를 찾을 수 없습니다.")

        print(f"✅ [UserFetcher] 사용자 조회: {user.get('user_name')}")
        return user


# =========================================
# Analyzer 
# =========================================
@dataclass
class Analyzer:
    verbose: bool = False

    def analyze(
        self,
        conversation_df: pd.DataFrame,
        relations: List[Dict[str, Any]],
        id: int
    ) -> Dict[str, Any]:

        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)

        # 분석 대상 사용자 DF
        user_df = conversation_df[conversation_df["speaker"] == int(id)]
        if user_df.empty:
            raise ValueError(f"❌ id={id}의 발화가 없습니다.")

        # 화자별 분리 → other를 한데 모으지 않음
        other_speakers = sorted(
            list(set(conversation_df["speaker"].tolist()) - {int(id)})
        )

        others_grouped_stats = {}
        for spk in other_speakers:
            spk_df = conversation_df[conversation_df["speaker"] == spk]
            spk_text = " ".join(spk_df["text"].tolist())
            spk_words = extract_content_words_korean(spk_text)
            others_grouped_stats[str(spk)] = {
                "token_count": len(spk_words),
                "mattr": calculate_mattr_korean(spk_words),
                "unique_content_words": len(set(spk_words)),
                "top_content_words": Counter(spk_words).most_common(5)
            }

        # 🔧 user 통계 계산
        user_text = " ".join(user_df["text"].tolist())
        user_words = extract_content_words_korean(user_text)

        user_stats = {
            "token_count": len(user_words),
            "mattr": calculate_mattr_korean(user_words),
            "unique_content_words": len(set(user_words)),
            "top_content_words": Counter(user_words).most_common(5)
        }

        # 🔧 comparison
        comparison = {
            "user_mattr": user_stats["mattr"],
            "others_mattr": {
                spk: stats["mattr"] for spk, stats in others_grouped_stats.items()
            }
        }

        # 🔧 전체 statistics JSON
        statistics = {
            "user": user_stats,
            "others": others_grouped_stats,
            "comparison": comparison
        }

        # ================================
        # 스타일 분석 (🔥 통계 결과 포함하여 프롬프트 강화)
        # ================================
        full_context = "\n".join([
            f"화자 {row['speaker']}: {row['text']}"
            for _, row in conversation_df.iterrows()
        ])
        user_texts_joined = "\n".join(user_df["text"].tolist())

        statistics_json_str = json.dumps(statistics, ensure_ascii=False, indent=2)

        style_prompt = f"""
다음은 대화 전체 내용입니다:

{full_context}

그리고 아래는 '사용자 ID {id}'의 발화만 모은 내용입니다:

{user_texts_joined}

또한, 형태소 기반 내용어 분석 + MATTR 기반 통계 분석 결과는 다음과 같습니다:

{statistics_json_str}

위의 대화 맥락, 사용자 발화, 통계 분석을 모두 고려하여
→ 사용자 ID {id}의 **말투, 표현 습관, 대화 스타일, 언어적 성향**을 구조화하여 분석해 주세요.

JSON 형식으로 작성해 주세요:
{{
  "말투": "...",
  "표현습관": "...",
  "대화스타일": "...",
  "언어적특징": "...",
  "종합평가": "..."
}}
"""

        try:
            resp = llm.invoke(style_prompt)
            raw = resp.content if hasattr(resp, "content") else str(resp)
            try:
                style_json = json.loads(raw)
            except:
                style_json = {"요약": raw[:200]}
            style_analysis = {str(id): style_json}
        except:
            style_analysis = {str(id): {"분석": "실패"}}

        # 🔧 기존 점수 계산 유지
        score = self._calculate_user_score(
            user_stats,
            {"token_count": sum(o["token_count"] for o in others_grouped_stats.values())},
            {}
        )

        summary = f"[요약] 사용자 MATTR={user_stats['mattr']:.3f}"

        return {
            "summary": summary,
            "style_analysis": style_analysis,
            "statistics": statistics,
            "score": score,
        }

    # =========================================
    # 기존 점수 계산 유지
    # =========================================
    def _calculate_user_score(self, user_stats, others_stats, user_analysis):
        vocab = user_stats["unique_content_words"] / max(1, user_stats["token_count"])
        score = vocab
        return round(min(1.0, max(0.0, score)), 2)


# =========================================
# ScoreEvaluator
# =========================================
@dataclass
class ScoreEvaluator:
    def evaluate(self, result: Dict[str, Any]) -> bool:
        return result.get("score", 0) >= 0.65


# =========================================
# AnalysisSaver
# =========================================
@dataclass
class AnalysisSaver:
    verbose: bool = False

    def save(self, db: Session, result: Dict[str, Any], state):
        if not result:
            return {"status": "no_result"}

        saved = save_analysis_result(
            db=db,
            id=str(state.id),
            conv_id=str(state.conv_id),
            summary=result["summary"],
            style_analysis=result["style_analysis"],
            statistics=result["statistics"],
            score=result["score"],
            confidence_score=0.0,
            conversation_count=len(state.conversation_df) if hasattr(state, "conversation_df") else 0
        )

        return {"status": "saved", "analysis_id": saved["analysis_id"]}
