# =========================================
# app/agent/Analysis/dialect_normalizer.py
# =========================================

from dataclasses import dataclass
import numpy as np
import pandas as pd
from typing import Dict, List, Any


@dataclass
class DialectProsodyNormalizer:
    """
    GAON Prosody Normalizer
    - observed_slope 계산
    - dialect likelihood (지역 방언 확률)
    - emotional deviation (감정 편차)
    - variation (turn-level 변화량)
    """

    # 🔵 방언별 baseline 구간 (기존 연구 기반)
    BASELINES = {
        "seoul": (-10, 0),
        "gyeongsang": (-30, -20),
        "chungcheong": (-12, -8),
        "jeolla": (-5, 5),
    }

    def _softmax(self, x):
        """수치 안정성 softmax"""
        e = np.exp(x - np.max(x))
        return e / e.sum()

    def normalize(self, merged_df: pd.DataFrame) -> Dict[str, Any]:
        """
        최종 반환:
        {
            "turn_prosody": [... turn-level prosody 결과 ...],
            "dialect_likelihood": {... 지역별 확률 ...},
            "baseline_region": "...",
            "baseline_slope_mean": float
        }
        """

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

            # 🔵 핵심 Feature: F0semitone variability
            observed = feats.get("F0semitoneFrom27.5Hz_sma3nz_stddevNorm", None)
            slopes.append(observed)

            results.append({
                "turn_index": idx,
                "speaker": row["speaker"],
                "observed_slope": observed,
            })

        # =========================================
        # 2) dialect likelihood 계산 (연구 기반)
        # =========================================
        valid_slopes = [s for s in slopes if s is not None]
        mean_obs = np.mean(valid_slopes) if valid_slopes else 0

        distances = {}
        for region, (lo, hi) in self.BASELINES.items():
            center = (lo + hi) / 2
            distances[region] = abs(mean_obs - center)

        neg_dist = np.array([-d for d in distances.values()])
        probs = self._softmax(neg_dist)

        dialect_likelihood = {
            region: float(prob)
            for region, prob in zip(self.BASELINES.keys(), probs)
        }

        # 🔥 가장 가능성 높은 지역
        baseline_region = max(dialect_likelihood, key=dialect_likelihood.get)
        baseline_mean = np.mean(self.BASELINES[baseline_region])

        # =========================================
        # 3) turn-level 감정 deviation, variation 계산
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
