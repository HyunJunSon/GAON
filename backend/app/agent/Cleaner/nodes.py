# ============================================
# app/agent/Cleaner/nodes.py  (FINAL REFACTORED)
# ============================================

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import pandas as pd
import json
import numpy as np
import librosa
import io

from sqlalchemy.orm import Session
from google.cloud import storage

# CRUD functions
from app.agent.crud import (
    get_conversation_by_id,
    get_conversation_file_by_conv_id,
    get_user_by_id,
)


# =======================================================
# 1) RawFetcher
# =======================================================
@dataclass
class RawFetcher:
    """
    - conversation / conversation_file 테이블로부터
      분석에 필요한 모든 RAW 데이터를 가져온다.
    - AnalysisGraph와 달리 Cleaner 단계에서는
      "메타 + 오디오 URL + speaker_segments + speaker_mapping" 만 가져오면 된다.
    """

    def fetch(self, db: Session, conv_id: str) -> Dict[str, Any]:

        if db is None:
            raise ValueError("❌ RawFetcher: db 세션이 없습니다.")
        if not conv_id:
            raise ValueError("❌ RawFetcher: conv_id 필요합니다.")

        # ------------------------------
        # 기본 conversation 메타 조회
        # ------------------------------
        meta = get_conversation_by_id(db, conv_id)
        if not meta:
            raise ValueError(f"❌ conversation row 없음 (conv_id={conv_id})")

        # ------------------------------
        # conversation_file 조회
        # ------------------------------
        file_row = get_conversation_file_by_conv_id(db, conv_id)
        if not file_row:
            raise ValueError(f"❌ conversation_file row 없음 (conv_id={conv_id})")

        audio_url = file_row.get("audio_url")
        speaker_segments = file_row.get("speaker_segments")
        speaker_mapping = file_row.get("speaker_mapping")

        if speaker_segments is None:
            raise ValueError("❌ speaker_segments 없음")
        if speaker_mapping is None:
            raise ValueError("❌ speaker_mapping 없음")

        # JSON decode
        if isinstance(speaker_segments, str):
            speaker_segments = json.loads(speaker_segments)
        if isinstance(speaker_mapping, str):
            speaker_mapping = json.loads(speaker_mapping)

        # ------------------------------
        # user_id / gender / age 자동 결정
        # ------------------------------
        user_self_id = None
        if "user_ids" in speaker_mapping and len(speaker_mapping["user_ids"]) > 0:
            # 항상 하나의 user_id만 있다고 가정
            user_self_id = list(speaker_mapping["user_ids"].values())[0]

        user_gender = None
        user_age = None
        user_name = None

        if user_self_id:
            user_obj = get_user_by_id(db, user_self_id)
            if user_obj:
                # SQLAlchemy row to dict
                user_gender = user_obj["gender"]
                user_age = user_obj["age"]
                user_name = user_obj["user_name"]

        # ------------------------------
        # Text-only DF 생성
        # ------------------------------
        df = pd.DataFrame([
            {"speaker": seg["speaker"], "text": seg["text"]}
            for seg in speaker_segments
        ])

        # ------------------------------
        # 반환
        # ------------------------------
        return {
            "df": df,
            "audio_url": audio_url,
            "speaker_segments": speaker_segments,
            "speaker_mapping": speaker_mapping,
            "user_self_id": user_self_id,
            "user_gender": user_gender,
            "user_age": user_age,
            "user_name": user_name,
        }


# =======================================================
# 2) DataInspector
# =======================================================
@dataclass
class DataInspector:
    """
    - 발화 턴이 3개 이상인지 간단 검증
    - issues 목록에 문제 추가
    """

    def inspect(self, df: pd.DataFrame, state=None):
        issues = []

        if df is None or len(df) < 3:
            issues.append("not_enough_turns")

        return df, issues


# =======================================================
# 3) TokenCounter
# =======================================================
@dataclass
class TokenCounter:
    """
    - 각 speaker의 어절 수가 최소 25개 이상인지 체크
    - 부족하면 issue 추가
    """

    def count(self, df: pd.DataFrame, state=None):
        issues = []

        if df is None:
            issues.append("df_is_none")
            return df, issues

        try:
            grouped = df.groupby("speaker")["text"].apply(
                lambda x: sum(len(s.split()) for s in x)
            )

            for spk, tcount in grouped.items():
                if tcount < 25:
                    issues.append(f"speaker_{spk}_not_enough_tokens")

        except Exception as e:
            issues.append(str(e))

        return df, issues


# =======================================================
# 4) AudioFeatureExtractor  (Librosa Version)
# =======================================================
@dataclass
class AudioFeatureExtractor:
    """
    - librosa 기반으로 pitch/energy/MFCC 계산
    """

    def _load_audio(self, audio_url: str):
        from app.core.config import settings

        bucket_name = settings.gcp_bucket_name
        client = storage.Client()
        blob = client.bucket(bucket_name).blob(audio_url)

        if not blob.exists():
            raise FileNotFoundError(f"❌ GCP Blob 없음: {audio_url}")

        audio_bytes = blob.download_as_bytes()
        y, sr = librosa.load(io.BytesIO(audio_bytes), sr=None)
        return y, sr

    # ---- Pitch ----
    def _pitch(self, y, sr):
        try:
            f0 = librosa.yin(y, fmin=50, fmax=500, sr=sr)
            f0 = f0[f0 > 0]

            if len(f0) == 0:
                return None, None

            return float(np.mean(f0)), float(np.std(f0))
        except:
            return None, None

    # ---- Energy ----
    def _energy(self, y):
        try:
            rms = librosa.feature.rms(y=y)
            return float(np.mean(rms))
        except:
            return None

    # ---- MFCC ----
    def _mfcc(self, y, sr, n=5):
        try:
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n)
            return [float(np.mean(v)) for v in mfcc]
        except:
            return [None] * n

    # ---- Extract ----
    def extract(self, audio_url: str, speaker_segments: List[Dict]) -> List[Dict]:

        y, sr = self._load_audio(audio_url)
        updated = []

        for seg in speaker_segments:

            start = seg.get("start", 0)
            end = seg.get("end", 0)

            start_idx = int(start * sr)
            end_idx = int(end * sr)

            chunk = y[start_idx:end_idx]

            if len(chunk) < sr * 0.1:
                seg["pitch_mean"] = None
                seg["pitch_std"] = None
                seg["energy"] = None
                seg["mfcc"] = [None] * 5
                updated.append(seg)
                continue

            mean_f0, std_f0 = self._pitch(chunk, sr)
            energy = self._energy(chunk)
            mfcc = self._mfcc(chunk, sr, 5)

            seg["pitch_mean"] = mean_f0
            seg["pitch_std"] = std_f0
            seg["energy"] = energy
            seg["mfcc"] = mfcc

            updated.append(seg)

        return updated


# =======================================================
# 5) ExceptionHandler
# =======================================================
@dataclass
class ExceptionHandler:
    """
    - 어떤 노드에서 에러가 나든 state.issues에 기록하고 진행 중단
    (CleanerGraph에서 조건문이 이를 처리)
    """

    def handle(self, state, err):
        state.issues.append(str(err))
        return state
