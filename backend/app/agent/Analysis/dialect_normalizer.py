from dataclasses import dataclass
import numpy as np
import pandas as pd
from typing import Dict, List, Any

@dataclass
class DialectProsodyNormalizer:
    """
    GAON Prosody Normalizer
    - observed_slope 계산
    - dialect likelihood
    - emotional deviation
    - variation (turn-level)
    """

    # baseline slope ranges (Hz/turn)
    BASELINES = {
        "seoul": (-10, 0),
        "gyeongsang": (-30, -20),
        "chungcheong": (-12, -8),
        "jeolla": (-5, 5),
    }

    def _mean_baseline(self, region: str) -> float:
        lo, hi = self.BASELINE[region]
        return (lo + hi) / 2

    def _softmax(self, x):
        e = np.exp(x - np.max(x))
        return e / e.sum()

    def normalize(self, merged_df: pd.DataFrame) -> Dict[str, Any]:
        results = []
        slopes = []

        for idx, row in merged_df.iterrows():
            feats = row.get("audio_features")
            if feats is None:
                # 텍스트-only turn
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

            # 1) observed slope = F0 semitone variability
            observed = feats.get("F0semitoneFrom27.5Hz_sma3nz_stddevNorm", None)
            slopes.append(observed)

            results.append({
                "turn_index": idx,
                "speaker": row["speaker"],
                "observed_slope": observed
            })

        # dialect likelihood 계산
        # 평균 observed slope (None 제외)
        valid_slopes = [s for s in slopes if s is not None]
        mean_obs = np.mean(valid_slopes) if valid_slopes else 0

        # 거리 기반 softmax
        distances = {}
        for region, (lo, hi) in self.BASELINES.items():
            target = (lo + hi) / 2
            distances[region] = abs(mean_obs - target)

        neg_dist = [-d for d in distances.values()]
        probs = self._softmax(np.array(neg_dist))

        dialect_likelihood = {
            region: float(prob) 
            for region, prob in zip(self.BASELINES.keys(), probs)
        }

        # 가장 높은 likelihood 지역 baseline 선택
        max_region = max(dialect_likelihood, key=dialect_likelihood.get)
        baseline_mean = np.mean(self.BASELINES[max_region])

        # 이제 감정 deviation, variation 계산
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

            # baseline slope
            r["baseline_slope"] = baseline_mean

            # deviation
            dev = slope - baseline_mean
            r["emotional_deviation"] = dev

            # variation
            if prev_slope is None:
                r["variation"] = 0
            else:
                r["variation"] = abs(slope - prev_slope)

            prev_slope = slope

            # emotion category
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
        }
