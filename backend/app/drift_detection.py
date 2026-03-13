from __future__ import annotations

import numpy as np
import pandas as pd
import ruptures as rpt

SIGNAL_COLUMNS = ["flow_frequency", "unique_destination_count", "unique_port_count"]


def _series_drift(series: pd.Series) -> tuple[float, list[int]]:
    values = series.astype(float).to_numpy()
    if len(values) < 5 or np.allclose(values, values[0]):
        return 0.0, []

    reshaped = values.reshape(-1, 1)
    penalty = max(1.0, float(np.std(values) * 1.5))
    change_points = [
        point
        for point in rpt.Pelt(model="rbf").fit(reshaped).predict(pen=penalty)
        if point < len(values)
    ]
    if not change_points:
        return 0.0, []

    latest_change = change_points[-1]
    if len(values) - latest_change > 3:
        return 0.15, change_points

    before = values[max(0, latest_change - 3):latest_change]
    after = values[latest_change:]
    if before.size == 0 or after.size == 0:
        return 0.2, change_points

    magnitude = abs(float(after.mean() - before.mean()))
    scale = max(float(np.std(values)), 1.0)
    score = min(1.0, 0.25 + magnitude / (scale * 3.0))
    return round(score, 3), change_points


def detect_drift(window_features: pd.DataFrame) -> dict[str, dict]:
    drift_results: dict[str, dict] = {}

    for device_id, device_windows in window_features.groupby("device_id"):
        ordered = device_windows.sort_values("window_start")
        signal_breakdown = {}
        change_points = {}
        signal_scores = []

        for signal in SIGNAL_COLUMNS:
            score, points = _series_drift(ordered[signal])
            signal_scores.append(score)
            signal_breakdown[signal] = score
            change_points[signal] = points

        drift_results[device_id] = {
            "device_id": device_id,
            "drift_score": round(float(np.mean(signal_scores)), 3),
            "signal_breakdown": signal_breakdown,
            "change_points": change_points,
        }

    return drift_results
