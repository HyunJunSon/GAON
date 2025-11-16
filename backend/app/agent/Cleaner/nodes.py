# app/agent/Cleaner/nodes.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Tuple
from app.core.config import settings  # ✅ LLM 키 사용
from langchain_openai import ChatOpenAI  # ✅ LLM 연결
import uuid

try:
    import pandas as pd
except Exception:
    pd = None

# ✅ DB 연동 추가
from sqlalchemy.orm import Session
from app.agent.crud import (
    get_conversation_by_id,
    get_conversation_by_pk,
    conversation_to_dataframe,
)


# =========================================
# ✅ RawFetcher (DB 연동)
# =========================================
@dataclass
class RawFetcher:
    """
    ✅ DB에서 conversation 조회
    
    변경 사항:
    - 기존: SAMPLE_DIALOG (하드코딩)
    - 변경: DB에서 conversation 조회
    """
    def fetch(self, db: Session = None, conv_id: str = None, *args, **kwargs) -> Any:
        if db is None:
            raise ValueError("❌ RawFetcher: db 세션이 필요합니다.")
        if not conv_id:
            raise ValueError("❌ RawFetcher: conv_id(UUID)가 필요합니다.")

        conversation = get_conversation_by_id(db, conv_id)
        if not conversation:
            raise ValueError(f"❌ RawFetcher: conversation을 찾을 수 없습니다. (conv_id={conv_id})")

        print(f"✅ [RawFetcher] 대화 조회 성공: {conversation['title'][:50]}...")
        df = conversation_to_dataframe(conversation)
        print(f"   → DataFrame 생성: {len(df)}개 발화")
        return df



# =========================================
# ✅ RawInspector (기존 유지)
# =========================================
@dataclass
class RawInspector:
    """화자, 업로더(id) 검증"""
    def inspect(self, raw: Any, state=None) -> Tuple[Any, List[str]]:
        issues: List[str] = []
        if pd is not None and isinstance(raw, pd.DataFrame):
            df = raw.copy()
            unique_speakers = set(df["speaker"].astype(str))

            # ✅ 화자 2명 이상인지 확인
            if len(unique_speakers) < 2:
                issues.append("not_enough_speakers")

            # ✅ 업로더(id)가 화자 중 포함되어 있는지 확인
            if state and getattr(state, "id", None):
                if str(state.id) not in unique_speakers:
                    issues.append("uploader_not_in_speakers")
            else:
                issues.append("missing_user_id")

            # ✅ timestamp 누락 여부
            if "timestamp" not in df.columns or df["timestamp"].isnull().any():
                issues.append("missing_timestamp")

            # ✅ 참여자 목록(user_ids) 갱신
            if state:
                state.user_ids = list(unique_speakers)

            return df, issues

        return raw, ["unsupported_raw_type"]


# =========================================
# ✅ ConversationCleaner (기존 유지)
# =========================================
@dataclass
class ConversationCleaner:
    """LLM을 사용해 문장 정제 및 노이즈 제거 (배치 처리 최적화)"""
    verbose: bool = False
    batch_size: int = 10  # 한 번에 처리할 문장 수

    def clean(self, df: Any, state=None) -> Any:
        if pd is not None and isinstance(df, pd.DataFrame):
            out = df.copy()
            llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)

            texts = out["text"].tolist()
            cleaned = []
            
            # 배치 단위로 처리
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                
                # 배치 프롬프트 생성
                batch_prompt = "다음 문장들에서 철자 오류나 이상한 기호를 자연스럽게 수정해줘. 각 문장을 번호와 함께 수정해서 반환해줘:\n\n"
                for j, text in enumerate(batch, 1):
                    batch_prompt += f"{j}. {text}\n"
                
                if self.verbose:
                    print(f"🪶 [Cleaner LLM 배치 {i//self.batch_size + 1}] {len(batch)}개 문장 처리 중...")
                
                try:
                    response = llm.invoke(batch_prompt)
                    cleaned_text = (
                        response.content
                        if hasattr(response, "content")
                        else str(response)
                    )
                    
                    # 응답에서 개별 문장 추출
                    batch_cleaned = self._parse_batch_response(cleaned_text, batch)
                    cleaned.extend(batch_cleaned)
                    
                    if self.verbose:
                        print(f"✅ [Cleaner LLM 배치 완료] {len(batch_cleaned)}개 문장 정제됨")
                        
                except Exception as e:
                    # 실패 시 원본 사용
                    cleaned.extend(batch)
                    print(f"⚠️ 배치 LLM 호출 실패: {e}")
            
            out["text"] = cleaned
            return out
        return df
    
    def _parse_batch_response(self, response: str, original_batch: List[str]) -> List[str]:
        """배치 응답에서 개별 문장 추출"""
        lines = response.strip().split('\n')
        cleaned_batch = []
        
        for i, original in enumerate(original_batch, 1):
            # 번호로 시작하는 라인 찾기
            found = False
            for line in lines:
                if line.strip().startswith(f"{i}."):
                    cleaned_text = line.strip()[2:].strip()  # "1. " 제거
                    cleaned_batch.append(cleaned_text)
                    found = True
                    break
            
            if not found:
                # 파싱 실패 시 원본 사용
                cleaned_batch.append(original)
        
        return cleaned_batch


# =========================================
# ✅ ConversationValidator (기존 유지)
# =========================================
@dataclass
class ConversationValidator:
    """대화의 분석 가능성 판단"""
    verbose: bool = False

    def validate(self, df: Any, state=None) -> Tuple[bool, List[str]]:
        issues: List[str] = []
        if pd is not None and isinstance(df, pd.DataFrame):
            # ✅ 티키타카 3세트(6회 이상) 여부
            speakers = df["speaker"].tolist()
            tiktaka = sum(speakers[i] != speakers[i - 1] for i in range(1, len(speakers)))
            if tiktaka < 6:
                issues.append("not_enough_tiktaka")

            llm_ok, reason = self._llm_judge(df)
            if not llm_ok:
                issues.append(f"llm_rejected:{reason}")
            return (len(issues) == 0), issues
        return False, ["unsupported_type"]

    def _llm_judge(self, df: Any) -> Tuple[bool, str]:
        """LLM으로 감정 분석 적합 여부 판단"""
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)
        text = "\n".join(df["text"].astype(str).tolist()[:6])
        prompt = f"다음 대화가 감정분석에 적합한가? '적합' 또는 '부적합'으로만 대답:\n{text}"
        try:
            response = llm.invoke(prompt)
            reply = response.content if hasattr(response, "content") else str(response)
            if self.verbose:
                print(f"🤖 [Validator LLM 응답] {reply}")
            return "부적합" not in reply, reply
        except Exception as e:
            return False, str(e)


# =========================================
# ✅ ConversationSaver (수정 - DB 이미 있으므로 스킵)
# =========================================
@dataclass
class ConversationSaver:
    """
    ✅ conversation 테이블에 저장 (이미 DB에 있으므로 현재는 스킵)
    
    변경 사항:
    - 기존: DataFrame → conversation 테이블 INSERT
    - 변경: 이미 DB에 있으므로 메타데이터만 state에 저장
    """
    def save(self, df: Any, state=None) -> Dict[str, Any]:
        """
        이미 DB에 conversation이 존재하므로 스킵
        state에 메타데이터만 저장
        """
        try:
            # ✅ 이미 DB에 저장되어 있으므로 메타정보만 반환
            if state and hasattr(state, "conv_id"):
                return {
                    "status": "already_saved",
                    "conversation_id": state.conv_id,
                    "message": "대화는 이미 DB에 저장되어 있습니다.",
                }
            
            return {"status": "skipped"}

        except Exception as e:
            return {"status": "error", "error": str(e)}


# =========================================
# ✅ ExceptionHandler 그대로 유지
# =========================================
@dataclass
class ExceptionHandler:
    """예외를 표준화하여 반환"""
    def handle(self, err: Exception) -> Dict[str, Any]:
        return {"status": "error", "error": str(err)}