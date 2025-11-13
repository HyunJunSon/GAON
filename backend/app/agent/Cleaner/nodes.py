# app/agent/Cleaner/nodes.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import pandas as pd

from sqlalchemy.orm import Session

# CRUD import
from app.agent.crud import (
    get_conversation_by_id,
    get_conversation_file_by_conv_id     # ← 신규 추가된 함수 사용
)



# =========================================
# ✅ RawFetcher 
# =========================================
@dataclass
class RawFetcher:
    """
    역할:
    - conversation → conversation_file로 접근
    - raw_content 가져와 DataFrame 생성
    - 파일 타입(text/audio) 분기 없음 (raw_content는 항상 텍스트)
    """

    def fetch(self, db: Session = None, conv_id: str = None, *args, **kwargs) -> pd.DataFrame:
        if db is None:
            raise ValueError("❌ RawFetcher: db 세션이 필요합니다.")
        if not conv_id:
            raise ValueError("❌ RawFetcher: conv_id(UUID)가 필요합니다.")

        # 1) conversation 메타 정보 조회
        meta = get_conversation_by_id(db, conv_id)
        if not meta:
            raise ValueError(f"❌ conversation 메타정보 없음 (conv_id={conv_id})")

        # 2) 🔧 conversation_file에서 원문(raw_content) 조회
        file_row = get_conversation_file_by_conv_id(db, conv_id)
        if not file_row:
            raise ValueError(f"❌ raw_content 없음 (conversation_file에 데이터 없음)")

        raw_text = file_row["raw_content"]
        if not raw_text:
            raise ValueError(f"❌ raw_content 비어 있음 (conv_id={conv_id})")

        # 3) 🔧 원문 텍스트를 DataFrame으로 파싱
        df = self._to_dataframe(raw_text)

        print(f"✅ [RawFetcher] raw_content 로드 완료 → {len(df)}개 발화")
        return df


    def _to_dataframe(self, raw_text: str) -> pd.DataFrame:
        """
        🔧 기존 conversation_to_dataframe 제거 → 여기로 통합
        변경 이유:
        - DB 구조가 conversation_file.raw_content로 단일화되었기 때문
        """

        lines = raw_text.strip().split("\n")

        data = []
        current_speaker = None
        current_text = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 예: "참석자 1:"
            if line.startswith("참석자"):
                if current_speaker is not None and current_text:
                    data.append({
                        "speaker": current_speaker,
                        "text": current_text.strip(),
                    })
                parts = line.split()
                current_speaker = int(parts[1].replace(":", ""))  # "1:" → 1
                current_text = ""
            else:
                current_text += line + " "

        if current_speaker is not None and current_text:
            data.append({
                "speaker": current_speaker,
                "text": current_text.strip(),
            })

        return pd.DataFrame(data)



# =========================================
# ✅ DataInspector (turn ≥ 3)
# =========================================
@dataclass
class DataInspector:
    def inspect(self, df: pd.DataFrame, state=None) -> Tuple[pd.DataFrame, List[str]]:
        issues = []

        # 🔧 발화 갯수(턴) 검증
        if len(df) < 3:
            issues.append("not_enough_turns")

        return df, issues



# =========================================
# ✅ TokenCounter (화자별 25 어절 이상)
# =========================================
@dataclass
class TokenCounter:
    def count(self, df: pd.DataFrame, state=None) -> Tuple[pd.DataFrame, List[str]]:
        issues = []
        
        # 화자별 어절수 계산
        grouped = df.groupby("speaker")["text"].apply(
            lambda x: sum(len(s.split()) for s in x)
        )

        for speaker, token_count in grouped.items():
            if token_count < 25:
                issues.append(f"speaker_{speaker}_not_enough_tokens")

        return df, issues



# =========================================
# ✅ ExceptionHandler
# =========================================
@dataclass
class ExceptionHandler:
    def handle(self, err: Exception) -> Dict[str, Any]:
        return {"status": "error", "error": str(err)}
