from __future__ import annotations

import pandas as pd


def _clamp(score: float) -> float:
    return max(0.0, min(100.0, score))


def _risk_level(score: float) -> str:
    if score < 40:
        return "critical"
    if score < 70:
        return "warning"
    return "safe"


def build_trust_scores(
    window_features: pd.DataFrame,
    baselines: dict[str, dict],
    drift_results: dict[str, dict],
    detections: dict[str, dict],
) -> tuple[dict[str, dict], dict[str, list[dict[str, float | str]]]]:
    device_scores: dict[str, dict] = {}
    histories: dict[str, list[dict[str, float | str]]] = {}

    for device_id, device_windows in window_features.groupby("device_id"):
        baseline = baselines[device_id]
        drift = drift_results[device_id]
        detection = detections[device_id]
        history: list[dict[str, float | str]] = []

        for _, row in device_windows.sort_values("window_start").iterrows():
            trust_score = 100.0
            flow_delta = abs(row["flow_frequency"] - baseline["average_flow_frequency"]) / max(
                baseline["average_flow_frequency"], 1.0
            )
            trust_score -= min(18.0, flow_delta * 14.0)

            unseen_destinations = len(set(row["destinations"]) - set(baseline["common_destinations"]))
            trust_score -= min(14.0, unseen_destinations * 4.0)

            unseen_ports = len(set(int(port) for port in row["ports"]) - set(baseline["normal_ports"]))
            trust_score -= min(12.0, unseen_ports * 4.0)

            if row["off_hours_ratio"] > 0.35:
                trust_score -= min(10.0, float(row["off_hours_ratio"]) * 12.0)
            if row["dns_queries"] > baseline["average_dns_queries"] * 2 + 1:
                trust_score -= 8.0
            if row["external_connection_ratio"] > baseline["average_external_ratio"] + 0.25:
                trust_score -= 10.0

            history.append(
                {
                    "timestamp": row["window_start"].isoformat(),
                    "trust_score": round(_clamp(trust_score), 2),
                }
            )

        current_score = history[-1]["trust_score"] if history else 100.0
        current_score -= drift["drift_score"] * 10.0
        current_score -= detection["botnet_probability"] * 40.0
        current_score -= min(15.0, detection["new_external_ip_count"] * 4.0)
        current_score -= min(10.0, detection["port_anomaly_count"] * 5.0)
        current_score = round(_clamp(current_score), 2)

        if history:
            history[-1]["trust_score"] = current_score

        device_scores[device_id] = {
            "device_id": device_id,
            "trust_score": current_score,
            "status": _risk_level(current_score),
            "risk_level": _risk_level(current_score),
            "drift_score": drift["drift_score"],
            "botnet_probability": detection["botnet_probability"],
            "anomalies": detection["anomalies"],
        }
        histories[device_id] = history

    return device_scores, histories
