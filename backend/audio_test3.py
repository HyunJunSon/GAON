# ============================================================
# 📌 test_audio_features.py
# Segment 기반 음향 피처 + 방언 기반 prosody normalization 테스트 코드
# ============================================================

import json
import numpy as np
import librosa

TEST_AUDIO_PATH = "./test_audio.webm"
TEST_SEGMENTS_JSON = "./segments.json"


# ============================================
# 1) Prosody Baseline (Dialect)
# ============================================

BASELINES = {
    "seoul": (-10, 0),
    "gyeongsang": (-30, -20),
    "chungcheong": (-12, -8),
    "jeolla": (-5, 5),
}


def softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum()


# ============================================
# 2) Feature Extractors
# ============================================

def extract_pitch(y, sr):
    try:
        pitch = librosa.yin(y, fmin=50, fmax=500, sr=sr)
        pitch = pitch[pitch > 0]
        return pitch
    except:
        return np.array([])


def extract_energy(y):
    try:
        rms = librosa.feature.rms(y=y)
        return float(np.mean(rms))
    except:
        return None


def extract_mfcc(y, sr, n_mfcc=5):
    try:
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        return [float(np.mean(x)) for x in mfcc]
    except:
        return [None] * n_mfcc


# ============================================
# 3) Segment Feature + Dialect Normalization
# ============================================

def extract_features_from_segments():

    print("🎧 오디오 로드...")
    y, sr = librosa.load(TEST_AUDIO_PATH, sr=None)

    with open(TEST_SEGMENTS_JSON, "r", encoding="utf-8") as f:
        segments_data = json.load(f)

    segments = segments_data["speaker_segments"]

    results = []

    # ---------------------------
    # Segment-level prosody slope 저장
    # ---------------------------
    slopes = []

    for idx, seg in enumerate(segments):
        print(f"\n---------------- Segment {idx} ----------------")
        print(seg)

        start = seg["start"]
        end = seg["end"]

        start_idx = int(start * sr)
        end_idx = int(end * sr)
        chunk = y[start_idx:end_idx]

        # pitch array
        pitch_arr = extract_pitch(chunk, sr)

        if len(pitch_arr) == 0:
            observed_slope = None
            pitch_mean = None
        else:
            pitch_mean = float(np.mean(pitch_arr))
            observed_slope = float(np.std(pitch_arr))   # ⭐ pitch 변화량 기반 slope

        slopes.append(observed_slope)

        features = {
            "speaker": seg["speaker"],
            "start": start,
            "end": end,
            "pitch_mean": pitch_mean,
            "pitch_std": observed_slope,   # slope proxy
            "energy": extract_energy(chunk),
            "mfcc": extract_mfcc(chunk, sr, 5),
        }

        results.append(features)

        # ===========================
    # 🔥 Dialect Likelihood 계산 (print 강화)
    # ===========================

    print("\n\n=================== DIALECT ESTIMATION DEBUG ===================")

    # 1) observed slope summary
    print("\n[1] Segment-level observed_slopes (pitch_std):")
    for i, s in enumerate(slopes):
        print(f"  - seg[{i}] slope = {s}")

    valid_slopes = [s for s in slopes if s is not None]
    mean_obs = np.mean(valid_slopes) if valid_slopes else 0
    print(f"\n[2] mean observed slope = {mean_obs}")

    # 2) baseline comparison
    print("\n[3] Distance to each region baseline center:")
    distances = {}
    for region, (lo, hi) in BASELINES.items():
        center = (lo + hi) / 2
        dist = abs(mean_obs - center)
        distances[region] = dist
        print(f"  * {region} center={center}, dist={dist}")

    # 3) softmax normalization
    print("\n[4] Softmax Input Vector (negative distance):")
    neg = np.array([-d for d in distances.values()])
    print("   neg_dist =", neg)

    probs = softmax(neg)

    print("\n[5] Softmax Output (dialect likelihood):")
    dialect_likelihood = {}
    for (region, _), p in zip(BASELINES.items(), probs):
        dialect_likelihood[region] = float(p)
        print(f"  → {region}: {p}")

    # 4) final chosen
    baseline_region = max(dialect_likelihood, key=dialect_likelihood.get)
    baseline_mean = np.mean(BASELINES[baseline_region])

    print("\n[6] Chosen Baseline Region:", baseline_region)
    print("    Baseline Region Slope Mean:", baseline_mean)
    print("===============================================================\n")


    # ===========================
    # 🔥 Emotional Deviation 계산
    # ===========================

    prev = None
    for res in results:
        slope = res["pitch_std"]

        if slope is None:
            res["emotional_deviation"] = None
            res["variation"] = None
            continue

        dev = slope - baseline_mean
        res["emotional_deviation"] = dev

        if prev is None:
            res["variation"] = 0
        else:
            res["variation"] = abs(slope - prev)

        prev = slope

    # ===========================
    # 최종 출력
    # ===========================

    out = {
        "segments": results,
        "dialect_likelihood": dialect_likelihood,
        "baseline_region": baseline_region,
        "baseline_mean_slope": baseline_mean,
        "mean_observed_slope": mean_obs,
    }

    print("\n================== FINAL RESULT ==================")
    print(json.dumps(out, indent=2, ensure_ascii=False))

    return out


if __name__ == "__main__":
    extract_features_from_segments()
