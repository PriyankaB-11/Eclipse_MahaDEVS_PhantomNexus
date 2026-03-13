from __future__ import annotations

from statistics import mean, pstdev

import pandas as pd

SUSPICIOUS_PORTS = {23, 2323, 48101, 5555, 6667}


def _periodic_beacon_detected(
    device_flows: pd.DataFrame,
    internal_ips: set[str],
    baseline_destinations: set[str],
) -> tuple[bool, dict]:
    external_flows = device_flows[
        ~device_flows["dest_ip"].isin(internal_ips)
        & ~device_flows["dest_ip"].isin(baseline_destinations)
    ].copy()
    if external_flows.empty:
        return False, {}

    for destination, destination_flows in external_flows.groupby("dest_ip"):
        ordered = destination_flows.sort_values("timestamp")
        if len(ordered) < 6:
            continue
        deltas = ordered["timestamp"].diff().dropna().dt.total_seconds().tolist()
        if len(deltas) < 5:
            continue
        avg_delta = mean(deltas)
        if avg_delta == 0:
            continue
        variance = pstdev(deltas)
        if avg_delta <= 1200 and variance / avg_delta < 0.18:
            return True, {
                "beacon_destination": destination,
                "avg_interval_seconds": round(avg_delta, 2),
                "variance_ratio": round(variance / avg_delta, 3),
            }

    return False, {}


def detect_botnet_patterns(
    telemetry: pd.DataFrame,
    window_features: pd.DataFrame,
    baselines: dict[str, dict],
) -> dict[str, dict]:
    internal_ips = set(telemetry["src_ip"].unique())
    latest_windows = (
        window_features.sort_values("window_start").groupby("device_id").tail(1).set_index("device_id")
    )
    detections: dict[str, dict] = {}

    for device_id, device_flows in telemetry.groupby("device_id"):
        baseline = baselines[device_id]
        latest_window = latest_windows.loc[device_id]
        recent_flows = device_flows.sort_values("timestamp").tail(max(18, len(device_flows) // 3))

        reasons: list[str] = []
        evidence: dict[str, object] = {}
        probability = 0.0

        latest_destinations = set(latest_window["destinations"])
        baseline_destinations = set(baseline["common_destinations"])
        recent_external_destinations = {
            destination
            for destination in recent_flows["dest_ip"].tolist()
            if destination not in internal_ips
        }
        new_external_ips = sorted(
            destination
            for destination in recent_external_destinations - baseline_destinations
        )
        if new_external_ips:
            reasons.append("new external IP")
            evidence["new_external_ips"] = new_external_ips
            probability += min(0.28, 0.08 * len(new_external_ips))

        latest_ports = set(int(port) for port in recent_flows["dest_port"].tolist())
        suspicious_port_hits = sorted(latest_ports & SUSPICIOUS_PORTS)
        if suspicious_port_hits:
            reasons.append("suspicious ports")
            evidence["suspicious_ports"] = suspicious_port_hits
            probability += min(0.22, 0.11 * len(suspicious_port_hits))

        periodic, beacon_evidence = _periodic_beacon_detected(
            recent_flows,
            internal_ips,
            baseline_destinations,
        )
        if periodic:
            reasons.append("periodic beaconing detected")
            evidence["beaconing"] = beacon_evidence
            probability += 0.32

        dns_destinations = recent_flows[recent_flows["dest_port"] == 53]["dest_ip"].nunique()
        if dns_destinations > max(3, baseline["average_dns_queries"] * 3):
            reasons.append("DNS anomaly")
            evidence["dns_unique_destinations"] = int(dns_destinations)
            probability += 0.18

        recent_external_ratio = float((~recent_flows["dest_ip"].isin(internal_ips)).mean())
        if recent_external_ratio > max(0.72, baseline["average_external_ratio"] + 0.22):
            reasons.append("external outreach spike")
            evidence["external_connection_ratio"] = round(recent_external_ratio, 3)
            probability += 0.14

        if latest_destinations - baseline_destinations:
            probability += 0.08

        detections[device_id] = {
            "device_id": device_id,
            "botnet_probability": round(min(probability, 0.99), 3),
            "anomalies": reasons,
            "evidence": evidence,
            "new_external_ip_count": len(new_external_ips),
            "port_anomaly_count": len(suspicious_port_hits),
        }

    return detections
