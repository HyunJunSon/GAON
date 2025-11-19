from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import pandas as pd
import io
import json
import numpy as np
import librosa
from sqlalchemy.orm import Session
from google.cloud import storage

# CRUD
from app.agent.crud import (
    get_conversation_by_id,
    get_conversation_file_by_conv_id,
    get_user_by_id,
)


# ===============================================================
# 🔥 1) RawFetcher (대폭 수정)
# ===============================================================
@dataclass
class RawFetcher:

    def fetch(self, db: Session, conv_id: str) -> Dict[str, Any]:

        if db is None:
            raise ValueError("❌ RawFetcher: db 세션이 없습니다.")
        if not conv_id:
            raise ValueError("❌ RawFetcher: conv_id 필요")

        # ---- DB 조회 ----
        meta = get_conversation_by_id(db, conv_id)
        if not meta:
            raise ValueError(f"❌ conversation row 없음 (conv_id={conv_id})")

        file_row = get_conversation_file_by_conv_id(db, conv_id)
        if not file_row:
            raise ValueError(f"❌ conversation_file 없음 (conv_id={conv_id})")

        audio_url = file_row.get("audio_url")
        speaker_segments = file_row.get("speaker_segments")
        speaker_mapping = file_row.get("speaker_mapping")

        if speaker_segments is None:
            raise ValueError("❌ speaker_segments 필드가 없습니다.")
        if speaker_mapping is None:
            raise ValueError("❌ speaker_mapping 필드가 없습니다.")

        # JSON 처리
        if isinstance(speaker_segments, str):
            speaker_segments = json.loads(speaker_segments)
        if isinstance(speaker_mapping, str):
            speaker_mapping = json.loads(speaker_mapping)

        # speaker_mapping 구조:
        # {
        #   "speaker_names": { "SPEAKER_0A": "나", "SPEAKER_0B": "친구" },
        #   "user_ids": { "SPEAKER_0A": 9 }
        # }
        user_self_id = None
        if "user_ids" in speaker_mapping:
            if len(speaker_mapping["user_ids"]) > 0:
                # "나" 라인 하나뿐이므로 첫 번째 user_id
                user_self_id = list(speaker_mapping["user_ids"].values())[0]

        # user 정보 조회 (성별/나이)
        user_gender = None
        user_age = None
        if user_self_id:
            user_obj = get_user_by_id(db, user_self_id)
            if user_obj:
                user_gender = user_obj["gender"]   
                user_age = user_obj["age"]  

        # ---- DataInspector, TokenCounter 유지 위해 DF 생성
        df = pd.DataFrame([
            {"speaker": seg["speaker"], "text": seg["text"]}
            for seg in speaker_segments
        ])

        return {
            "df": df,
            "audio_url": audio_url,                 # 내부 처리용 (출력 x)
            "speaker_segments": speaker_segments,   # 원본 segments
            "speaker_mapping": speaker_mapping,
            "user_self_id": user_self_id,
            "user_gender": user_gender,
            "user_age": user_age,
        }



# ===============================================================
# 2) DataInspector — 유지
# ===============================================================
@dataclass
class DataInspector:
    def inspect(self, df: pd.DataFrame, state=None):
        issues = []
        if len(df) < 3:
            issues.append("not_enough_turns")
        return df, issues



# ===============================================================
# 3) TokenCounter — 유지
# ===============================================================
@dataclass
class TokenCounter:
    def count(self, df: pd.DataFrame, state=None):
        issues = []
        grouped = df.groupby("speaker")["text"].apply(
            lambda x: sum(len(s.split()) for s in x)
        )
        for spk, tcount in grouped.items():
            if tcount < 25:
                issues.append(f"speaker_{spk}_not_enough_tokens")
        return df, issues



# ===============================================================
# 4) AudioFeatureExtractor (🔥 openSMILE 제거 → librosa로 재작성)
# ===============================================================
@dataclass
class AudioFeatureExtractor:

    # GCP에서 오디오 로딩
    def _load_audio(self, audio_url: str):
        from app.core.config import settings

        bucket_name = settings.gcp_bucket_name
        client = storage.Client()
        blob = client.bucket(bucket_name).blob(audio_url)

        if not blob.exists():
            raise FileNotFoundError(f"❌ blob 없음: {audio_url}")

        audio_bytes = blob.download_as_bytes()

        y, sr = librosa.load(io.BytesIO(audio_bytes), sr=None)
        return y, sr


    # ---- Feature extraction ----
    def _pitch(self, y, sr):
        try:
            f0 = librosa.yin(y, fmin=50, fmax=500, sr=sr)
            f0 = f0[f0 > 0]
            if len(f0) == 0:
                return None, None
            return float(np.mean(f0)), float(np.std(f0))
        except:
            return None, None

    def _energy(self, y):
        try:
            rms = librosa.feature.rms(y=y)
            return float(np.mean(rms))
        except:
            return None

    def _mfcc(self, y, sr, n=5):
        try:
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n)
            return [float(np.mean(v)) for v in mfcc]
        except:
            return [None] * n


    def extract(self, audio_url: str, speaker_segments: List[Dict]) -> List[Dict]:

        y, sr = self._load_audio(audio_url)

        updated_segments = []

        for seg in speaker_segments:

            start = seg.get("start")
            end = seg.get("end")

            start_idx = int(start * sr)
            end_idx = int(end * sr)

            chunk = y[start_idx:end_idx]

            # 최소 길이 필터링
            if len(chunk) < sr * 0.1:
                seg["pitch_mean"] = None
                seg["pitch_std"] = None
                seg["energy"] = None
                seg["mfcc"] = [None] * 5
                updated_segments.append(seg)
                continue

            mean_f0, std_f0 = self._pitch(chunk, sr)
            energy = self._energy(chunk)
            mfcc = self._mfcc(chunk, sr, 5)

            seg["pitch_mean"] = mean_f0
            seg["pitch_std"] = std_f0
            seg["energy"] = energy
            seg["mfcc"] = mfcc

            updated_segments.append(seg)

        return updated_segments



# ===============================================================
# 5) ExceptionHandler
# ===============================================================
@dataclass
class ExceptionHandler:
    def handle(self, state, err):
        state.issues.append(str(err))
        state.validated = False
        return state
