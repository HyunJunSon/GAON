# =========================================
# app/agent/Analysis/dialect_normalizer.py
# =========================================

from dataclasses import dataclass
import numpy as np
import pandas as pd
from typing import Dict, Any


@dataclass
class DialectProsodyNormalizer:
    """
    GAON Prosody Normalizer
    """

    BASELINES = {
        "seoul": (-10, 0),
        "gyeongsang": (-30, -20),
        "chungcheong": (-12, -8),
        "jeolla": (-5, 5),
    }

    # 🔥 threshold: baseline과의 최소 거리가 이 이상이면 방언이 아님
    THRESHOLD = 20  # 기본값 (pitch_std 기준)

    def _softmax(self, x):
        e = np.exp(x - np.max(x))
        return e / e.sum()

    def normalize(self, merged_df: pd.DataFrame) -> Dict[str, Any]:

        results = []
        slopes = []

        # =========================================
        # 1) turn-level slope 추출
        # =========================================
        for idx, row in merged_df.iterrows():
            feats = row.get("audio_features")

            if feats is None:
                results.append({
                    "turn_index": idx,
                    "speaker": row["speaker"],
                    "observed_slope": None,
                    "baseline_slope": None,
                    "emotional_deviation": None,
                    "variation": None,
                    "emotion_category": "none",
                })
                slopes.append(None)
                continue

            observed = feats.get("pitch_std", None)  # 수정됨
            slopes.append(observed)

            results.append({
                "turn_index": idx,
                "speaker": row["speaker"],
                "observed_slope": observed,
            })

        # =========================================
        # 2) dialect likelihood 계산
        # =========================================
        valid_slopes = [s for s in slopes if s is not None]
        mean_obs = np.mean(valid_slopes) if valid_slopes else 0

        distances = {}
        for region, (lo, hi) in self.BASELINES.items():
            center = (lo + hi) / 2
            distances[region] = abs(mean_obs - center)

        # 가장 가까운 baseline
        min_region = min(distances, key=distances.get)
        min_dist = distances[min_region]

        # ================================
        # 🔥 핵심 변경: baseline 밖이면 서울 표준어로 강제 처리
        # ================================
        if min_dist > self.THRESHOLD:
            baseline_region = "seoul_standard"
            baseline_mean = -5  # 표준어 중심
            dialect_likelihood = {"seoul_standard": 1.0}

        else:
            # 기존 방식 유지
            neg = np.array([-d for d in distances.values()])
            probs = self._softmax(neg)

            dialect_likelihood = {
                region: float(prob)
                for region, prob in zip(self.BASELINES.keys(), probs)
            }

            baseline_region = min_region
            baseline_mean = np.mean(self.BASELINES[baseline_region])

        # =========================================
        # 3) 감정 deviation 계산
        # =========================================
        prev_slope = None
        for r in results:
            slope = r.get("observed_slope")

            if slope is None:
                r.update({
                    "baseline_slope": None,
                    "emotional_deviation": None,
                    "variation": None,
                    "emotion_category": "none",
                })
                continue

            r["baseline_slope"] = baseline_mean

            dev = slope - baseline_mean
            r["emotional_deviation"] = dev

            if prev_slope is None:
                r["variation"] = 0
            else:
                r["variation"] = abs(slope - prev_slope)

            prev_slope = slope

            abs_dev = abs(dev)
            if abs_dev < 5:
                cat = "stable"
            elif abs_dev < 10:
                cat = "mild"
            elif abs_dev < 20:
                cat = "medium"
            else:
                cat = "strong"

            r["emotion_category"] = cat

        return {
            "turn_prosody": results,
            "dialect_likelihood": dialect_likelihood,
            "baseline_region": baseline_region,
            "baseline_slope_mean": baseline_mean,
            "mean_observed_slope": mean_obs,
        }
