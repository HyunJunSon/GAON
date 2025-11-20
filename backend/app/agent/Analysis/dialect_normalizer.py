from dataclasses import dataclass
import numpy as np
from typing import Dict, Any, List


@dataclass
class DialectProsodyNormalizer:
    BASELINES = {
        "seoul": (-10, 0),
        "gyeongsang": (-30, -20),
        "chungcheong": (-12, -8),
        "jeolla": (-5, 5),
    }

    THRESHOLD = 20

    def _softmax(self, x):
        e = np.exp(x - np.max(x))
        return e / e.sum()

    def normalize(self, speaker_segments: List[Dict[str, Any]]) -> Dict[str, Any]:

        results = []
        slopes = []

        # 1) turn-level slope
        for idx, seg in enumerate(speaker_segments):
            pitch_std = seg.get("pitch_std")

            slopes.append(pitch_std)

            results.append({
                "turn_index": idx,
                "speaker": seg.get("speaker"),
                "observed_slope": pitch_std,
            })

        # 2) baseline 계산
        valid_slopes = [s for s in slopes if s is not None]
        mean_obs = np.mean(valid_slopes) if valid_slopes else 0

        distances = {}
        for region, (lo, hi) in self.BASELINES.items():
            center = (lo + hi) / 2
            distances[region] = abs(mean_obs - center)

        min_region = min(distances, key=distances.get)
        min_dist = distances[min_region]

        if min_dist > self.THRESHOLD:
            baseline_region = "seoul_standard"
            baseline_mean = -5
            dialect_likelihood = {"seoul_standard": 1.0}
        else:
            neg = np.array([-d for d in distances.values()])
            probs = self._softmax(neg)

            dialect_likelihood = {
                region: float(prob)
                for region, prob in zip(self.BASELINES.keys(), probs)
            }

            baseline_region = min_region
            baseline_mean = np.mean(self.BASELINES[min_region])

        # 3) 감정 deviation
        prev_slope = None
        for r in results:
            slope = r["observed_slope"]

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

            r["variation"] = 0 if prev_slope is None else abs(slope - prev_slope)
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
