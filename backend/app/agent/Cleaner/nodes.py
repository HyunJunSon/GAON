# app/agent/Cleaner/nodes.py 

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
import requests
import librosa

from sqlalchemy.orm import Session

# CRUD
from app.agent.crud import (
    get_conversation_by_id,
    get_conversation_file_by_conv_id,
)


# ===============================================================
# 1) RawFetcher
# ===============================================================
@dataclass
class RawFetcher:
    """
    DB에서 conversation_file.raw_content 및 file_type/audio_url/speaker_segments 를 읽어
    → DataFrame(df)와 메타 정보 반환
    """

    def fetch(self, db: Session = None, conv_id: str = None, *args, **kwargs) -> Dict[str, Any]:
        if db is None:
            raise ValueError("❌ RawFetcher: db 세션이 필요합니다.")
        if not conv_id:
            raise ValueError("❌ RawFetcher: conv_id(UUID)가 필요합니다.")

        meta = get_conversation_by_id(db, conv_id)
        if not meta:
            raise ValueError(f"❌ conversation 메타정보 없음 (conv_id={conv_id})")

        file_row = get_conversation_file_by_conv_id(db, conv_id)
        if not file_row:
            raise ValueError(f"❌ conversation_file row 없음 (conv_id={conv_id})")

        # DB에 저장된 정보 사용
        file_type = file_row.get("file_type")
        audio_url = file_row.get("audio_url")
        speaker_segments = file_row.get("speaker_segments")
        raw_text = file_row.get("raw_content")

        if not raw_text:
            raise ValueError(f"❌ raw_content 비어 있음 (conv_id={conv_id})")

        df = self._to_dataframe(raw_text)

        print(f"✅ [RawFetcher] raw_content 로드 완료 → {len(df)}개 발화")

        return {
            "df": df,
            "file_type": file_type,
            "audio_url": audio_url,
            "speaker_segments": speaker_segments,
        }

    # ===============================================================
    def _to_dataframe(self, raw_text: str) -> pd.DataFrame:
        lines = raw_text.strip().split("\n")

        data = []
        current_speaker = None
        current_text = ""

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("참석자"):
                if current_speaker is not None and current_text:
                    data.append({
                        "speaker": current_speaker,
                        "text": current_text.strip(),
                    })
                parts = line.split()
                current_speaker = int(parts[1].replace(":", ""))
                current_text = ""
            else:
                current_text += line + " "

        if current_speaker is not None and current_text:
            data.append({
                "speaker": current_speaker,
                "text": current_text.strip(),
            })

        return pd.DataFrame(data)


# ===============================================================
# 2) DataInspector (turn ≥ 3)
# ===============================================================
@dataclass
class DataInspector:
    def inspect(self, df: pd.DataFrame, state=None) -> Tuple[pd.DataFrame, List[str]]:
        issues = []
        if len(df) < 3:
            issues.append("not_enough_turns")
        return df, issues


# ===============================================================
# 3) TokenCounter (speaker별 25 tokens)
# ===============================================================
@dataclass
class TokenCounter:
    def count(self, df: pd.DataFrame, state=None) -> Tuple[pd.DataFrame, List[str]]:
        issues = []
        grouped = df.groupby("speaker")["text"].apply(
            lambda x: sum(len(s.split()) for s in x)
        )

        for spk, tcount in grouped.items():
            if tcount < 25:
                issues.append(f"speaker_{spk}_not_enough_tokens")

        return df, issues


# ===============================================================
# 4) FileTypeClassifier
# ===============================================================
@dataclass
class FileTypeClassifier:
    """
    DB file_type 기반으로 text/audio 여부 판별
    """

    ALLOWED_AUDIO = ["wav", "mp3", "webm", "m4a"]
    ALLOWED_TEXT = ["txt", "pdf", "doc", "docx"]

    def classify(self, file_type: str) -> str:
        if not file_type:
            raise ValueError("❌ file_type 없음")

        file_type = file_type.lower()

        if file_type in self.ALLOWED_AUDIO:
            return "audio"
        if file_type in self.ALLOWED_TEXT:
            return "text"

        raise ValueError(f"❌ 지원하지 않는 파일 타입: {file_type}")


# ===============================================================
# 5) AudioFeatureExtractor
# ===============================================================
@dataclass
class AudioFeatureExtractor:
    """
    speaker_segments = [
        {"speaker": 1, "start": 0.0, "end": 2.4},
        {"speaker": 2, "start": 2.5, "end": 4.2},
    ]
    audio_url에서 구간별 audio 신호를 잘라서 특징 추출
    """

    def extract(self, audio_url: str, speaker_segments: List[Dict]) -> List[Dict]:

        if not audio_url:
            raise ValueError("❌ audio_url 없음 (audio 파일이 아님)")

        # GCP URL 다운로드
        resp = requests.get(audio_url)
        if resp.status_code != 200:
            raise ValueError("❌ audio_url 다운로드 실패")

        audio_bytes = resp.content

        # librosa로 로드 (메모리 스트림)
        import io
        y, sr = librosa.load(io.BytesIO(audio_bytes), sr=None)

        features = []

        for seg in speaker_segments or []:
            start = int(seg["start"] * sr)
            end = int(seg["end"] * sr)
            chunk = y[start:end]

            if len(chunk) == 0:
                continue

            # 특징 추출
            pitch = librosa.yin(chunk, fmin=50, fmax=500).mean()
            energy = float(np.mean(chunk ** 2))
            tempo, _ = librosa.beat.beat_track(y=chunk, sr=sr)

            features.append({
                "speaker": seg["speaker"],
                "start": seg["start"],
                "end": seg["end"],
                "pitch": float(pitch),
                "energy": energy,
                "tempo": float(tempo),
            })

        print(f"🎛️ [AudioFeatureExtractor] {len(features)}개 발화 audio 특징 추출 완료")
        return features


# ===============================================================
# 6) ContentValidator (텍스트 전용)
# ===============================================================
@dataclass
class ContentValidator:
    """
    텍스트 전용 후처리 (필요하면 추가 규칙 적용 가능)
    """
    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        # 현재는 그대로 pass
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


# ===============================================================
# 7) ContentMerger (text + audio features)
# ===============================================================
@dataclass
class ContentMerger:
    """
    audio_features 를 speaker-match 기반으로 df에 merge
    """

    def merge(self, text_df: pd.DataFrame, audio_features: Optional[List[Dict]]) -> pd.DataFrame:

        df = text_df.copy()
        df["pitch"] = None
        df["energy"] = None
        df["tempo"] = None

        if audio_features:
            for feat in audio_features:
                spk = feat["speaker"]

                # 해당 speaker의 첫 번째 발화에 붙이기
                idx_list = df.index[df["speaker"] == spk].tolist()
                if not idx_list:
                    continue

                first_idx = idx_list[0]
                df.at[first_idx, "pitch"] = feat["pitch"]
                df.at[first_idx, "energy"] = feat["energy"]
                df.at[first_idx, "tempo"] = feat["tempo"]

        return df


# ===============================================================
# ExceptionHandler
# ===============================================================
@dataclass
class ExceptionHandler:
    def handle(self, err: Exception) -> Dict[str, Any]:
        return {"status": "error", "error": str(err)}

