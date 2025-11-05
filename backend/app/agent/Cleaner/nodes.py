from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Tuple
from app.core.config import settings  # ✅ LLM 키 사용
from langchain_openai import ChatOpenAI  # ✅ LLM 연결
import uuid  # ✅ ConversationSaver용 UUID 생성

try:
    import pandas as pd
except Exception:
    pd = None


# =========================================
# ✅ 샘플 대화 (노이즈 일부 포함)
# =========================================
SAMPLE_DIALOG = [
    ("201", "오늘 하루 어땠어?/\d\d", "2025-11-04 18:10:00"),
    ("202", "음… 그냥 평범했어. 회사 일 좀 많았어.", "2025-11-04 18:11:10"),
    ("201", "요즘 피곤해 보이 네. 괜찮아?", "2025-11-04 18:12:00"),
    ("202", "응, 괜찮아. 그냥 잠을 좀 못 잤어.", "2025-11-04 18:13:00"),
    ("203", "엄마아아, 나 숙제 다 했어!", "2025-11-04 18:14:20"),
    ("201", "우리 아들 최고야이네! 이제 놀아도 돼~", "2025-11-04 18:15:00"),
    ("202", "하하, 고마워. 너 덕분에 힘난다.", "2025-11-04 18:16:40"),
]


# =========================================
# ✅ RawFetcher
# =========================================
@dataclass
class RawFetcher:
    """샘플 데이터를 불러와 DataFrame으로 반환"""
    def fetch(self, *args, **kwargs) -> Any:
        if pd is not None:
            df = pd.DataFrame(
                [{"speaker": s, "text": t, "timestamp": ts} for s, t, ts in SAMPLE_DIALOG]
            )
            return df
        return SAMPLE_DIALOG


# =========================================
# ✅ RawInspector
# =========================================
@dataclass
class RawInspector:
    """화자, 업로더(user_id) 검증"""
    def inspect(self, raw: Any, state=None) -> Tuple[Any, List[str]]:
        issues: List[str] = []
        if pd is not None and isinstance(raw, pd.DataFrame):
            df = raw.copy()
            unique_speakers = set(df["speaker"].astype(str))

            # ✅ 화자 2명 이상인지 확인
            if len(unique_speakers) < 2:
                issues.append("not_enough_speakers")

            # ✅ 업로더(user_id)가 화자 중 포함되어 있는지 확인
            if state and getattr(state, "user_id", None):
                if str(state.user_id) not in unique_speakers:
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
# ✅ ConversationCleaner (LLM 연결)
# =========================================
@dataclass
class ConversationCleaner:
    """LLM을 사용해 문장 정제 및 노이즈 제거"""
    verbose: bool = False

    def clean(self, df: Any, state=None) -> Any:
        if pd is not None and isinstance(df, pd.DataFrame):
            out = df.copy()
            llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key)

            cleaned = []
            for text in out["text"]:
                prompt = f"다음 문장에서 철자 오류나 이상한 기호를 자연스럽게 수정해줘:\n{text}"
                if self.verbose:
                    print(f"🪶 [Cleaner LLM 입력] {text}")
                try:
                    response = llm.invoke(prompt)
                    cleaned_text = (
                        response.content
                        if hasattr(response, "content")
                        else str(response)
                    )
                    cleaned.append(cleaned_text)
                    if self.verbose:
                        print(f"✅ [Cleaner LLM 결과] {cleaned_text}")
                except Exception as e:
                    cleaned.append(text)
                    print(f"⚠️ LLM 호출 실패: {e}")
            out["text"] = cleaned
            return out
        return df


# =========================================
# ✅ ConversationValidator (LLM 판단)
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
# ✅ ConversationSaver (DB 매핑형 구조로 리팩토링)
# =========================================
@dataclass
class ConversationSaver:
    """conversation 테이블 구조에 맞게 정제된 데이터를 변환"""
    def save(self, df: Any, state=None) -> Dict[str, Any]:
        try:
            if pd is not None and isinstance(df, pd.DataFrame):
                conv_id = uuid.uuid4()
                raw_id = uuid.uuid4()  # ✅ 추후 raw table 연동 시 수정
                created_at = datetime.utcnow()
                updated_at = created_at

                conv_start = pd.to_datetime(df["timestamp"]).min()
                conv_end = pd.to_datetime(df["timestamp"]).max()

                cont_content = "\n".join(
                    [f"{r['speaker']}: {r['text']}" for _, r in df.iterrows()]
                )
                cont_title = df.iloc[0]["text"][:30] + "..."

                user_id = getattr(state, "user_id", None)
                conv_create_id = user_id

                record = {
                    "conv_id": str(conv_id),
                    "cont_title": cont_title,
                    "cont_content": cont_content,
                    "conv_start": conv_start,
                    "conv_end": conv_end,
                    "conv_create_id": str(conv_create_id),
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "user_id": str(user_id),
                    "raw_id": str(raw_id),
                }

                conv_df = pd.DataFrame([record])
                state.meta["conversation_df"] = conv_df

                return {
                    "status": "saved",
                    "conversation_id": str(conv_id),
                    "rows": len(conv_df),
                    "record": record,
                }

            return {"status": "noop"}

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
