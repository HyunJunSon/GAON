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
# ✅ FamilyChecker (DB 연동) --> 임시로 항상 Faslse 반환하게 구현됨
# =========================================
# =========================================
# ✅ FamilyChecker (가족 기능 비활성화)
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
# ✅ RelationResolver_LLM (기존 유지)
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
# ✅ Analyzer
# =========================================
@dataclass
class Analyzer:
    """감정/스타일/통계 분석"""
    verbose: bool = False

    def analyze(self, conversation_df: pd.DataFrame, relations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        LLM으로 대화 분석
        
        🔧 수정 사항:
        1. statistics 생성 (단어 수, 평균 문장 길이 등)
        2. style_analysis 생성 (화자별 말투/성향/관심사)
        3. summary 생성 (LLM 기반 대화 요약)
        
        Args:
            conversation_df: 대화 DataFrame
            relations: 관계 정보
        
        Returns:
            분석 결과 (DB 스키마 준수)
        """
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)
        
        # =========================================
        # 1️⃣ statistics 생성 (기본 통계)
        # =========================================
        # 이유: 대화의 정량적 특징 분석
        # =========================================
        
        all_texts = " ".join(conversation_df["text"].tolist())
        words = all_texts.split()
        
        statistics = {
            "word_count": len(words),  # 총 단어 수
            "avg_sentence_length": round(len(words) / len(conversation_df), 1),  # 평균 문장 길이
            "unique_words": len(set(words)),  # 고유 단어 수
            "top_words": self._get_top_words(all_texts, top_n=5)  # 빈도 높은 단어 5개
        }
        
        if self.verbose:
            print(f"   📊 [Statistics] 단어 수: {statistics['word_count']}, "
                  f"고유 단어: {statistics['unique_words']}")
        
        # =========================================
        # 2️⃣ style_analysis 생성 (화자별 분석)
        # =========================================
        # 이유: 각 화자의 말투/성향/관심사 분석
        # =========================================
        
        style_analysis = {}
        
        # 화자별로 분석
        unique_speakers = conversation_df["speaker"].unique()
        
        for speaker in unique_speakers:
            speaker_texts = conversation_df[conversation_df["speaker"] == speaker]["text"].tolist()
            speaker_text_joined = "\n".join(speaker_texts)
            
            # LLM 프롬프트
            prompt = f"""
다음 대화에서 화자 {speaker}의 말투, 성향, 관심사를 분석해줘.

화자 {speaker}의 발화:
{speaker_text_joined}

아래 형식으로 JSON 응답해줘:
{{
  "말투_특징_분석": "존댓말/반말 사용, 특정 표현 습관 등",
  "대화_성향_및_감정_표현": "긍정적/부정적, 격려/비판 성향 등",
  "주요_관심사": "대화 주제와 관심사"
}}
"""
            
            try:
                response = llm.invoke(prompt)
                content = response.content if hasattr(response, "content") else str(response)
                
                if self.verbose:
                    print(f"   🗣️ [Style Analysis] 화자 {speaker}: {content[:100]}...")
                
                # JSON 파싱 시도
                import json
                try:
                    speaker_analysis = json.loads(content)
                except:
                    # JSON 파싱 실패 시 fallback
                    speaker_analysis = {
                        "말투_특징_분석": content[:100],
                        "대화_성향_및_감정_표현": "분석 중",
                        "주요_관심사": "분석 중"
                    }
                
                style_analysis[str(speaker)] = speaker_analysis
                
            except Exception as e:
                print(f"⚠️ 화자 {speaker} 스타일 분석 LLM 실패: {e}")
                style_analysis[str(speaker)] = {
                    "말투_특징_분석": "분석 실패",
                    "대화_성향_및_감정_표현": "분석 실패",
                    "주요_관심사": "분석 실패"
                }
        
        # =========================================
        # 3️⃣ summary 생성 (전체 대화 요약)
        # =========================================
        # 이유: 대화 전체 맥락 파악
        # =========================================
        
        full_text = "\n".join([
            f"화자 {row['speaker']}: {row['text']}"
            for _, row in conversation_df.iterrows()
        ])
        
        summary_prompt = f"""
다음 대화를 100-200자로 요약해줘. 주요 주제와 분위기를 포함해줘.

대화:
{full_text}

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
        # 4️⃣ score 계산 (간단한 점수 산정)
        # =========================================
        # 이유: 대화 품질 점수화
        # =========================================
        
        # 간단한 점수 로직 (추후 개선 가능)
        score = min(1.0, (statistics["word_count"] / 100) * 0.5 + 0.5)
        score = round(score, 2)
        
        # =========================================
        # ✅ 최종 결과 반환
        # =========================================
        
        return {
            "summary": summary,
            "style_analysis": style_analysis,
            "statistics": statistics,
            "score": score,
        }
    
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
# ✅ ScoreEvaluator (기존 유지)
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
# ✅ AnalysisSaver (DB 연동)
# =========================================
@dataclass
class AnalysisSaver:
    """
    ✅ DB에 분석 결과 저장
    
    변경 사항:
    - 기존: Mock analysis_result_df
    - 변경: DB analysis_result 테이블 INSERT
    """
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
            # ✅ DB INSERT
            saved = save_analysis_result(
                db=db,
                user_id=str(state.user_id),
                conv_id=str(state.conv_id),
                summary=result.get("summary", ""),
                style_analysis=result.get("style_analysis", {}),
                statistics={},  # 추후 추가
                score=result.get("score", 0.0),
                confidence_score=0.0,  # QA에서 업데이트
                conversation_count=len(state.conversation_df) if state.conversation_df is not None else 0,
                feedback=None,
            )
            
            print(f"✅ [AnalysisSaver] DB 저장 완료: analysis_id={saved['analysis_id']}")
            
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