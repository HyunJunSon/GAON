# ============================================================
# 📌 test_audio_features.py
# Segment 기반 음향 피처 추출 테스트 코드
# ============================================================

import json
import numpy as np
import librosa
import os

# --------------------------------------
# 1) 기본 설정
# --------------------------------------
TEST_AUDIO_PATH = "./test_audio.webm"
TEST_SEGMENTS_JSON = "./segments.json"

# segments 로드 후 추가하는 코드

# Segment JSON 불러오기
with open(TEST_SEGMENTS_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

# 🔥 반드시 speaker_segments로 꺼내기
if isinstance(data, dict) and "speaker_segments" in data:
    segments = data["speaker_segments"]
else:
    segments = data

print(f"📌 총 {len(segments)}개 segments 분석 시작")

# 🔥 요소가 string이면 JSON 재파싱
if len(segments) > 0 and isinstance(segments[0], str):
    print("⚠ 요소가 문자열 → dict로 재파싱 진행")
    segments = [json.loads(s) for s in segments]

# --------------------------------------
# Pitch (YIN)
# --------------------------------------
def extract_pitch(y, sr):
    try:
        pitch = librosa.yin(
            y,
            fmin=50,
            fmax=500,
            sr=sr,
        )
        pitch = pitch[pitch > 0]
        return float(np.mean(pitch)) if len(pitch) > 0 else None
    except:
        return None


# --------------------------------------
# Energy (RMS)
# --------------------------------------
def extract_energy(y):
    try:
        rms = librosa.feature.rms(y=y)
        return float(np.mean(rms))
    except:
        return None


# --------------------------------------
# MFCC (5개만)
# --------------------------------------
def extract_mfcc(y, sr, n_mfcc=5):
    try:
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        return [float(np.mean(x)) for x in mfcc]
    except:
        return [None] * n_mfcc
    
# --------------------------------------
# 2) Pitch 추출 (YIN)
# --------------------------------------
def extract_features_from_segments():
    print("🎧 테스트 오디오 로드 중...")
    y, sr = librosa.load(TEST_AUDIO_PATH, sr=None)
    print(f"✔ 로드 완료: sr={sr}, length={len(y)} samples")

    # -------------------------
    # 🔥 segments.json 로드
    # -------------------------
    with open(TEST_SEGMENTS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("로드된 JSON 타입:", type(data))

    # 🔥 반드시 speaker_segments 리스트로 변환
    if isinstance(data, dict) and "speaker_segments" in data:
        segments = data["speaker_segments"]
    else:
        segments = data  # 혹시 이미 list면 그대로

    print("segments 타입:", type(segments))
    print("segments 길이:", len(segments))
    print("첫 element:", segments[0])
    print("첫 element 타입:", type(segments[0]))

    # 🔥 요소가 문자열(JSON string)이면 dict로 재파싱
    if isinstance(segments[0], str):
        print("⚠ 요소가 문자열 → dict 재파싱")
        segments = [json.loads(s) for s in segments]

    # -------------------------
    # 🔥 이제 절대 dict key iterate 하지 않음
    # -------------------------
    results = []

    for idx, seg in enumerate(segments):
        print(f"\n---------------- Segment {idx} ----------------")
        print(seg)

        # seg가 여전히 문자열이면 바로 오류 발생 → 안전장치
        if not isinstance(seg, dict):
            raise TypeError(f"❌ seg가 dict가 아님: {seg}")

        start = seg["start"]
        end   = seg["end"]

        start_idx = int(start * sr)
        end_idx   = int(end * sr)

        chunk = y[start_idx:end_idx]

        if len(chunk) < sr * 0.1:
            print("⚠ 너무 짧은 segment → SKIP")
            continue

        features = {
            "speaker": seg["speaker"],
            "start": start,
            "end": end,
            "pitch": extract_pitch(chunk, sr),
            "energy": extract_energy(chunk),
            "mfcc": extract_mfcc(chunk, sr, 5),
        }

        print("🎯 Extracted Features:")
        print(features)

        results.append(features)

    print("\n================== FINAL RESULT ==================")
    print(json.dumps(results, indent=2, ensure_ascii=False))

    return results



if __name__ == "__main__":
    extract_features_from_segments()
