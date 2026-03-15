from __future__ import annotations

import numpy as np
import pandas as pd
import ruptures as rpt

SIGNAL_COLUMNS = ["flow_frequency", "unique_destination_count", "unique_port_count"]


def _recent_shift_score(values: np.ndarray, tail_size: int = 3) -> float:
    if len(values) < 3:
        return 0.0

    # Keep head and tail non-empty even for short timelines.
    safe_tail = max(1, min(tail_size, len(values) // 2))

    head = values[:-safe_tail]
    tail = values[-safe_tail:]
    if head.size == 0 or tail.size == 0:
        return 0.0

    magnitude = abs(float(tail.mean() - head.mean()))
    # Keep the denominator stable so low-variance signals can still produce usable drift scores.
    scale = max(float(np.std(head)), 0.8)
    normalized = magnitude / scale
    return round(float(min(1.0, normalized / 4.0)), 3)


def _series_drift(series: pd.Series) -> tuple[float, list[int]]:
    values = series.astype(float).to_numpy()
    if np.allclose(values, values[0]):
        return 0.0, []

    recent_shift = _recent_shift_score(values)
    if len(values) < 5:
        return recent_shift, []

    reshaped = values.reshape(-1, 1)
    penalty = max(0.8, float(np.std(values) * 1.1))
    change_points = [
        point
        for point in rpt.Pelt(model="rbf").fit(reshaped).predict(pen=penalty)
        if point < len(values)
    ]
    if not change_points:
        # Even without explicit change points, capture smaller but persistent recent shifts.
        return recent_shift, []

    latest_change = change_points[-1]
    if len(values) - latest_change > 3:
        return round(max(0.15, recent_shift * 0.8), 3), change_points

    before = values[max(0, latest_change - 3):latest_change]
    after = values[latest_change:]
    if before.size == 0 or after.size == 0:
        return round(max(0.2, recent_shift), 3), change_points

    magnitude = abs(float(after.mean() - before.mean()))
    scale = max(float(np.std(values)), 1.0)
    cp_score = min(1.0, 0.25 + magnitude / (scale * 3.0))
    score = max(cp_score, recent_shift)
    return round(score, 3), change_points


def _sequence_churn_score(series: pd.Series) -> float:
    if len(series) < 2:
        return 0.0

    sets = [set(values or []) for values in series.tolist()]
    distances: list[float] = []
    for previous, current in zip(sets, sets[1:]):
        universe = previous | current
        if not universe:
            distances.append(0.0)
            continue
        overlap = len(previous & current) / len(universe)
        distances.append(1.0 - overlap)

    if not distances:
        return 0.0

    recent = distances[-3:]
    return round(float(min(1.0, np.mean(recent) * 1.2)), 3)


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

        if "destinations" in ordered.columns:
            destination_churn = _sequence_churn_score(ordered["destinations"])
            signal_scores.append(destination_churn)
            signal_breakdown["destination_churn"] = destination_churn
            change_points["destination_churn"] = []

        if "ports" in ordered.columns:
            port_churn = _sequence_churn_score(ordered["ports"])
            signal_scores.append(port_churn)
            signal_breakdown["port_churn"] = port_churn
            change_points["port_churn"] = []

        drift_results[device_id] = {
            "device_id": device_id,
            "drift_score": round(float(np.mean(signal_scores)), 3),
            "signal_breakdown": signal_breakdown,
            "change_points": change_points,
        }

    return drift_results
