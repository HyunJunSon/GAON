# app/agent/Analysis/nodes.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
from app.core.config import settings
from langchain_openai import ChatOpenAI
import pandas as pd

# =====================================
# ✅ Mock Database (ERD 기반)
# =====================================
user_df = pd.DataFrame([
    {"user_id": "201", "user_name": "김수정", "fam_id": "F001"},
    {"user_id": "202", "user_name": "이현수", "fam_id": "F001"},
    {"user_id": "203", "user_name": "김지우", "fam_id": "F002"},
])

family_df = pd.DataFrame([
    {"fam_id": "F001", "fam_name": "김씨네"},
    {"fam_id": "F002", "fam_name": "이씨네"},
])

analysis_result_df = pd.DataFrame(columns=[
    "analysis_id", "user_id", "conv_id", "summary", "style_analysis", "score"
])

# =====================================
# ✅ UserFetcher: 사용자 정보 로드
# =====================================
@dataclass
class UserFetcher:
    def fetch(self, conv_state) -> Dict[str, Any]:
        user_id = conv_state.user_id
        user = user_df[user_df["user_id"] == user_id]
        if user.empty:
            raise ValueError(f"User {user_id} not found.")
        return user.iloc[0].to_dict()

# =====================================
# ✅ FamilyChecker: 가족 관계 존재 여부 확인
# =====================================
@dataclass
class FamilyChecker:
    def check(self, user_info: Dict[str, Any]) -> Tuple[bool, str]:
        fam_id = user_info.get("fam_id")
        if fam_id and fam_id in family_df["fam_id"].values:
            return True, fam_id
        return False, None

# =====================================
# ✅ RelationResolver_DB: DB 기반 가족 매핑
# =====================================
@dataclass
class RelationResolver_DB:
    def resolve(self, fam_id: str) -> List[Dict[str, Any]]:
        related_users = user_df[user_df["fam_id"] == fam_id]
        return related_users.to_dict(orient="records")

# =====================================
# ✅ RelationResolver_LLM: LLM 기반 관계 추론
# =====================================
@dataclass
class RelationResolver_LLM:
    verbose: bool = False

    def resolve(self, conversation_df: pd.DataFrame) -> List[Dict[str, Any]]:
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)
        text_snippet = "\n".join(conversation_df["text"].tolist()[:5])
        prompt = f"""
        다음 대화에서 등장하는 인물들의 관계를 추론해줘.
        예: 아들, 엄마, 아빠, 친구 등
        대화 내용:
        {text_snippet}
        결과를 JSON 형태로 반환해줘. (예: [{{"speaker":"201","relation":"엄마"}}, ...])
        """
        try:
            response = llm.invoke(prompt)
            return [{"speaker": "201", "relation": "엄마"}, {"speaker": "203", "relation": "아들"}]
        except Exception as e:
            print(f"⚠️ Relation LLM 실패: {e}")
            return []

# =====================================
# ✅ Analyzer: 감정/스타일/통계 분석
# =====================================
@dataclass
class Analyzer:
    verbose: bool = False

    def analyze(self, conversation_df: pd.DataFrame, relations: List[Dict[str, Any]]) -> Dict[str, Any]:
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)
        text = "\n".join(conversation_df["text"].tolist())
        prompt = f"""
        다음 대화의 감정/어휘 스타일/대화 톤을 분석해줘.
        분석결과를 JSON 형식으로 반환 (emotion, tone, style, score 포함)
        대화 내용:
        {text}
        """
        try:
            response = llm.invoke(prompt)
            return {
                "summary": "따뜻한 가족 간 대화",
                "style_analysis": {"emotion": "긍정적", "tone": "편안함"},
                "score": 0.82,
            }
        except Exception as e:
            print(f"⚠️ 분석 LLM 실패: {e}")
            return {}

# =====================================
# ✅ ScoreEvaluator: 신뢰도 평가
# =====================================
@dataclass
class ScoreEvaluator:
    def evaluate(self, result: Dict[str, Any]) -> bool:
        return result.get("score", 0) >= 0.65

# =====================================
# ✅ AnalysisSaver: 결과 저장
# =====================================
@dataclass
class AnalysisSaver:
    def save(self, result: Dict[str, Any], state):
        global analysis_result_df
        new_row = {
            "analysis_id": len(analysis_result_df) + 1,
            "user_id": state.user_id,
            "conv_id": state.conv_id,
            "summary": result.get("summary"),
            "style_analysis": result.get("style_analysis"),
            "score": result.get("score"),
        }
        analysis_result_df = pd.concat(
            [analysis_result_df, pd.DataFrame([new_row])], ignore_index=True
        )
        state.meta["analysis_result"] = analysis_result_df
        return {"status": "saved", "rows": len(analysis_result_df)}
