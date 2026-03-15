from __future__ import annotations

from collections import Counter

import pandas as pd

from .data_loader import build_device_ip_index


def _resolve_window_size(telemetry: pd.DataFrame, default_window_size: str) -> str:
    min_timestamp = telemetry["timestamp"].min()
    max_timestamp = telemetry["timestamp"].max()
    if pd.isna(min_timestamp) or pd.isna(max_timestamp):
        return default_window_size

    span_minutes = (max_timestamp - min_timestamp).total_seconds() / 60.0
    # For short uploads, use smaller windows so drift and baseline logic still have enough timeline points.
    if span_minutes <= 120:
        return "10min"
    if span_minutes <= 480:
        return "20min"
    return default_window_size


def _mode_hour(hours: pd.Series) -> int:
    if hours.empty:
        return 0
    mode = hours.mode()
    return int(mode.iloc[0]) if not mode.empty else int(hours.iloc[0])


def _top_distribution(values: pd.Series, limit: int = 5) -> dict[str, float]:
    counts = Counter(str(value) for value in values)
    total = sum(counts.values()) or 1
    return {
        key: round(value / total, 3)
        for key, value in counts.most_common(limit)
    }


def engineer_device_windows(telemetry: pd.DataFrame, window_size: str = "1h") -> pd.DataFrame:
    effective_window_size = _resolve_window_size(telemetry, window_size)
    internal_ips = set(telemetry["src_ip"].unique())
    windowed = telemetry.copy()
    windowed["window_start"] = windowed["timestamp"].dt.floor(effective_window_size)
    windowed["activity_hour"] = windowed["timestamp"].dt.hour
    windowed["is_external"] = ~windowed["dest_ip"].isin(internal_ips)
    windowed["is_off_hours"] = windowed["activity_hour"].isin([0, 1, 2, 3, 4, 5, 22, 23])

    grouped = windowed.groupby(["device_id", "window_start"], sort=True)
    features = grouped.agg(
        flow_frequency=("dest_ip", "size"),
        unique_destination_count=("dest_ip", "nunique"),
        avg_bytes_per_flow=("bytes", "mean"),
        avg_packets_per_flow=("packets", "mean"),
        unique_port_count=("dest_port", "nunique"),
        dns_queries=("dest_port", lambda series: int((series == 53).sum())),
        external_connection_ratio=("is_external", "mean"),
        off_hours_ratio=("is_off_hours", "mean"),
        time_of_day_activity=("activity_hour", _mode_hour),
    ).reset_index()

    latest_ips, ip_to_device = build_device_ip_index(telemetry)
    metadata = (
        grouped.apply(
            lambda frame: pd.Series(
                {
                    "destinations": sorted({str(value) for value in frame["dest_ip"]}),
                    "ports": sorted({int(value) for value in frame["dest_port"]}),
                    "port_distribution": _top_distribution(frame["dest_port"]),
                    "new_internal_targets": sorted(
                        {
                            ip_to_device[ip]
                            for ip in frame["dest_ip"]
                            if ip in ip_to_device and ip_to_device[ip] != frame.name[0]
                        }
                    ),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    features = features.merge(metadata, on=["device_id", "window_start"], how="left")
    features["latest_src_ip"] = features["device_id"].map(latest_ips)

    return features.sort_values(["device_id", "window_start"]).reset_index(drop=True)
