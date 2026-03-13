from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd


def build_behavioral_baselines(window_features: pd.DataFrame) -> dict[str, dict]:
    baselines: dict[str, dict] = {}

    for device_id, device_windows in window_features.groupby("device_id"):
        ordered = device_windows.sort_values("window_start").reset_index(drop=True)
        baseline_window_count = max(4, int(len(ordered) * 0.6))
        baseline_slice = ordered.iloc[:baseline_window_count]

        port_counter: Counter[int] = Counter()
        destination_counter: Counter[str] = Counter()
        for ports in baseline_slice["ports"]:
            port_counter.update(ports)
        for destinations in baseline_slice["destinations"]:
            destination_counter.update(destinations)

        active_hours = sorted({int(value) for value in baseline_slice["time_of_day_activity"].tolist()})
        baselines[device_id] = {
            "device_id": device_id,
            "normal_ports": [port for port, _ in port_counter.most_common(6)],
            "common_destinations": [destination for destination, _ in destination_counter.most_common(8)],
            "average_flow_frequency": round(float(baseline_slice["flow_frequency"].mean()), 3),
            "average_destination_count": round(float(baseline_slice["unique_destination_count"].mean()), 3),
            "average_unique_port_count": round(float(baseline_slice["unique_port_count"].mean()), 3),
            "average_dns_queries": round(float(baseline_slice["dns_queries"].mean()), 3),
            "average_external_ratio": round(float(baseline_slice["external_connection_ratio"].mean()), 3),
            "normal_time_patterns": active_hours,
        }

    return baselines


def build_digital_twins(
    window_features: pd.DataFrame,
    baselines: dict[str, dict],
    trust_scores: dict[str, dict],
    drift_results: dict[str, dict],
    detections: dict[str, dict],
) -> dict[str, dict[str, Any]]:
    digital_twins: dict[str, dict[str, Any]] = {}

    for device_id, windows in window_features.groupby("device_id"):
        ordered = windows.sort_values("window_start").reset_index(drop=True)
        latest_window = ordered.iloc[-1]
        baseline = baselines[device_id]
        trust_payload = trust_scores[device_id]
        drift_payload = drift_results[device_id]
        detection_payload = detections[device_id]

        baseline_flow = max(float(baseline["average_flow_frequency"]), 1.0)
        baseline_destinations = set(str(item) for item in baseline["common_destinations"])
        baseline_ports = set(int(item) for item in baseline["normal_ports"])
        latest_destinations = set(str(item) for item in latest_window["destinations"])
        latest_ports = set(int(item) for item in latest_window["ports"])

        flow_delta_pct = ((float(latest_window["flow_frequency"]) - baseline_flow) / baseline_flow) * 100.0
        external_delta = float(latest_window["external_connection_ratio"]) - float(baseline["average_external_ratio"])

        trust_score = float(trust_payload["trust_score"])
        if trust_score < 40:
            behavioral_state = "compromised"
        elif trust_score < 70:
            behavioral_state = "degraded"
        else:
            behavioral_state = "stable"

        digital_twins[device_id] = {
            "device_id": device_id,
            "behavioral_state": behavioral_state,
            "confidence": round(max(0.0, 1.0 - drift_payload["drift_score"] * 0.8), 3),
            "baseline_profile": {
                "normal_ports": baseline["normal_ports"],
                "common_destinations": baseline["common_destinations"],
                "average_flow_frequency": baseline["average_flow_frequency"],
                "average_external_ratio": baseline["average_external_ratio"],
                "normal_time_patterns": baseline["normal_time_patterns"],
            },
            "observed_profile": {
                "window_start": latest_window["window_start"].isoformat(),
                "flow_frequency": int(latest_window["flow_frequency"]),
                "unique_destination_count": int(latest_window["unique_destination_count"]),
                "unique_port_count": int(latest_window["unique_port_count"]),
                "external_connection_ratio": round(float(latest_window["external_connection_ratio"]), 3),
                "time_of_day_activity": int(latest_window["time_of_day_activity"]),
            },
            "deviations": {
                "flow_frequency_delta_pct": round(flow_delta_pct, 2),
                "external_connection_delta": round(external_delta, 3),
                "new_destinations": sorted(latest_destinations - baseline_destinations),
                "new_ports": sorted(latest_ports - baseline_ports),
                "off_hours_ratio": round(float(latest_window["off_hours_ratio"]), 3),
            },
            "threat_overlay": {
                "trust_score": trust_payload["trust_score"],
                "risk_level": trust_payload["risk_level"],
                "drift_score": drift_payload["drift_score"],
                "botnet_probability": detection_payload["botnet_probability"],
                "anomalies": detection_payload["anomalies"],
            },
        }

    return digital_twins
