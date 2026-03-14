from __future__ import annotations

import ipaddress
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


SUSPICIOUS_PORTS = {23, 2323, 4444, 48101, 5555, 6667}
FEATURE_COLUMNS = [
    "connection_frequency",
    "unique_dest_ips",
    "avg_bytes",
    "avg_packets",
    "port_entropy",
    "time_of_day_activity",
    "beacon_interval_std",
    "external_ip_diversity",
    "suspicious_port_ratio",
    "off_hours_activity",
]


@dataclass
class BehaviorModelBundle:
    features: pd.DataFrame
    predictions: dict[str, dict]
    model: RandomForestClassifier


def _is_external_ip(ip_address_value: str) -> bool:
    try:
        return not ipaddress.ip_address(ip_address_value).is_private
    except ValueError:
        return True


def _shannon_entropy(values: pd.Series) -> float:
    probabilities = values.value_counts(normalize=True)
    if probabilities.empty:
        return 0.0
    return float(-(probabilities * np.log2(probabilities + 1e-12)).sum())


def _seconds_std(timestamps: pd.Series) -> float:
    ordered = timestamps.sort_values()
    intervals = ordered.diff().dropna().dt.total_seconds()
    if len(intervals) < 2:
        return 0.0
    return float(intervals.std(ddof=0) or 0.0)


def engineer_behavior_features(telemetry: pd.DataFrame) -> pd.DataFrame:
    device_frames: list[dict[str, float | int | str | list[str]]] = []

    for device_id, device_flows in telemetry.groupby("device_id"):
        ordered = device_flows.sort_values("timestamp")
        # These aggregates deliberately stay device-level so the hackathon model can train quickly after upload.
        span_seconds = max((ordered["timestamp"].max() - ordered["timestamp"].min()).total_seconds(), 3600.0)
        connection_frequency = len(ordered) / (span_seconds / 3600.0)
        unique_dest_ips = int(ordered["dest_ip"].nunique())
        avg_bytes = float(ordered["bytes"].mean())
        avg_packets = float(ordered["packets"].mean())
        port_entropy = _shannon_entropy(ordered["dest_port"])
        time_of_day_activity = float(ordered["timestamp"].dt.hour.mean())
        beacon_interval_std = _seconds_std(ordered["timestamp"])
        external_destinations = ordered[ordered["dest_ip"].map(_is_external_ip)]["dest_ip"].nunique()
        external_ip_diversity = float(external_destinations / max(len(ordered), 1))
        suspicious_port_ratio = float(ordered["dest_port"].isin(SUSPICIOUS_PORTS).mean())
        off_hours_activity = float(ordered["timestamp"].dt.hour.isin([0, 1, 2, 3, 4, 5, 22, 23]).mean())

        periodic_beaconing = beacon_interval_std <= 180.0 and connection_frequency >= 4.0
        high_external_ip_diversity = external_ip_diversity >= 0.18 or external_destinations >= 6
        unusual_ports = suspicious_port_ratio > 0 or ordered["dest_port"].nunique() >= 5

        anomaly_score = min(
            1.0,
            (0.35 if periodic_beaconing else 0.0)
            + min(0.35, external_ip_diversity * 1.6)
            + min(0.2, suspicious_port_ratio * 2.4)
            + min(0.1, off_hours_activity * 0.3),
        )

        device_frames.append(
            {
                "device_id": device_id,
                "connection_frequency": round(connection_frequency, 4),
                "unique_dest_ips": unique_dest_ips,
                "avg_bytes": round(avg_bytes, 4),
                "avg_packets": round(avg_packets, 4),
                "port_entropy": round(port_entropy, 4),
                "time_of_day_activity": round(time_of_day_activity, 4),
                "beacon_interval_std": round(beacon_interval_std, 4),
                "external_ip_diversity": round(external_ip_diversity, 4),
                "suspicious_port_ratio": round(suspicious_port_ratio, 4),
                "off_hours_activity": round(off_hours_activity, 4),
                "periodic_beaconing": periodic_beaconing,
                "high_external_ip_diversity": high_external_ip_diversity,
                "unusual_ports": unusual_ports,
                "heuristic_label": int(periodic_beaconing or high_external_ip_diversity or unusual_ports),
                "anomaly_score": round(anomaly_score, 4),
                "suspicious_ports": sorted({int(port) for port in ordered[ordered["dest_port"].isin(SUSPICIOUS_PORTS)]["dest_port"].tolist()}),
            }
        )

    return pd.DataFrame(device_frames).sort_values("device_id").reset_index(drop=True)


def _augment_training_rows(feature_frame: pd.DataFrame) -> pd.DataFrame:
    if feature_frame["heuristic_label"].nunique() > 1:
        return feature_frame

    # RandomForest needs at least two classes, so synthesize a contrast class when the upload is too uniform.
    augmented = feature_frame.copy()
    inverted = feature_frame.copy()
    inverted[FEATURE_COLUMNS] = inverted[FEATURE_COLUMNS].apply(
        lambda column: column * (0.75 if feature_frame["heuristic_label"].iloc[0] else 1.25)
    )
    inverted["heuristic_label"] = 1 - inverted["heuristic_label"]
    return pd.concat([augmented, inverted], ignore_index=True)


def train_behavior_model(feature_frame: pd.DataFrame) -> RandomForestClassifier:
    training_frame = _augment_training_rows(feature_frame)
    classifier = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        min_samples_leaf=1,
        random_state=42,
    )
    classifier.fit(training_frame[FEATURE_COLUMNS], training_frame["heuristic_label"])
    return classifier


def run_behavior_model(telemetry: pd.DataFrame) -> BehaviorModelBundle:
    feature_frame = engineer_behavior_features(telemetry)
    classifier = train_behavior_model(feature_frame)
    probabilities = classifier.predict_proba(feature_frame[FEATURE_COLUMNS])[:, 1]

    predictions: dict[str, dict] = {}
    for row, probability in zip(feature_frame.to_dict(orient="records"), probabilities, strict=True):
        detected_anomalies = []
        if row["periodic_beaconing"]:
            detected_anomalies.append("periodic beaconing")
        if row["high_external_ip_diversity"]:
            detected_anomalies.append("high external IP diversity")
        if row["unusual_ports"]:
            detected_anomalies.append("unusual ports")

        predictions[row["device_id"]] = {
            "device_id": row["device_id"],
            "botnet_probability": round(float(probability), 4),
            "anomaly_score": round(max(float(probability), float(row["anomaly_score"])), 4),
            "detected_anomalies": detected_anomalies,
            "feature_summary": {
                "connection_frequency": row["connection_frequency"],
                "unique_dest_ips": row["unique_dest_ips"],
                "avg_bytes": row["avg_bytes"],
                "avg_packets": row["avg_packets"],
                "port_entropy": row["port_entropy"],
                "time_of_day_activity": row["time_of_day_activity"],
                "beacon_interval_std": row["beacon_interval_std"],
            },
            "new_external_ip_count": int(math.ceil(row["external_ip_diversity"] * max(row["connection_frequency"], 1))),
            "port_anomaly_count": len(row["suspicious_ports"]),
            "suspicious_ports": row["suspicious_ports"],
        }

    return BehaviorModelBundle(features=feature_frame, predictions=predictions, model=classifier)